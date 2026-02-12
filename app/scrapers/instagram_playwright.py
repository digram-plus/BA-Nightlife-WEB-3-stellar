import asyncio
import os
import logging
from datetime import datetime
from playwright.async_api import async_playwright
from sqlalchemy.orm import Session
from ..db import SessionLocal
from ..models import Event
from ..genre import detect_genres
from ..utils import normalize_title, make_hash, parse_date
from ..services.ocr import extract_text_from_bytes
# from ..services.n8n_service import push_event_to_n8n

logger = logging.getLogger("instagram_playwright")
logging.basicConfig(level=logging.INFO)

async def scrape_profile(context, profile_name, limit=15, force_publish=False):
    page = await context.new_page()
    url = f"https://www.instagram.com/{profile_name}/"
    embed_url = f"https://www.instagram.com/{profile_name}/embed/"
    logger.info(f"Navigating to {url}")
    
    try:
        await page.goto(url, wait_until="networkidle", timeout=60000)
        # Give it a bit more time for posts to render if JS is slow
        await asyncio.sleep(5)
        
        # Check if we are blocked or redirected to login
        if "login" in page.url:
            logger.warning(f"Redirected to login for {profile_name}. Trying embed URL: {embed_url}")
            await page.goto(embed_url, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(5)
            
            if "login" in page.url:
                logger.error(f"Even embed URL redirected to login for {profile_name}. Giving up.")
                return 0

        # Select post elements
        # Profile view: 'div._aabd'
        # Embed view: 'a.EmbedGridItem', 'a.Embed', 'div.EmbedPost'
        try:
            await page.wait_for_selector('a[href*="/p/"], a[href*="/reel/"], .EmbeddedMediaImage', timeout=15000)
        except:
             logger.warning("Timeout waiting for post selectors. Proceeding with what we have.")

        posts = await page.query_selector_all('div._aabd')
        if not posts:
             # In embed view, images in the grid often have specific classes or are inside the Content div
             # We saw 'x5yr21d xu96u03 x10l6tqk x13vifvy x87ps6o xh8yej3' for post images
             all_imgs = await page.query_selector_all('img')
             # Skip the first one if it's the profile pic (it usually is)
             if len(all_imgs) > 1:
                 posts = all_imgs[1:]
             else:
                 posts = all_imgs
             
        logger.info(f"Found {len(posts)} potential posts for {profile_name}")
        
        db: Session = SessionLocal()
        created = 0
        try:
            for i, post in enumerate(posts[:limit]):
                try:
                    # 1. Extract Real Image URL (media_url)
                    # Try post first, then deeper
                    img_el = await post.query_selector('img')
                    tag_name = await post.evaluate("node => node.tagName")
                    if not img_el and tag_name == "IMG":
                        img_el = post

                    media_url = None
                    if img_el:
                        media_url = await img_el.get_attribute('src')
                    
                    # 2. Extract OCR text
                    # We use a new page to load the full image for better OCR accuracy
                    ocr_text = ""
                    if media_url:
                        img_page = await context.new_page()
                        try:
                            # Set a simple viewport for the image
                            await img_page.set_viewport_size({"width": 1080, "height": 1080})
                            await img_page.goto(media_url, wait_until="networkidle", timeout=30000)
                            # Take screenshot of the full image
                            ocr_bytes = await img_page.screenshot()
                            ocr_text = extract_text_from_bytes(ocr_bytes)
                        except Exception as ocr_err:
                            logger.error(f"OCR Error fetching image {media_url}: {ocr_err}")
                            # Fallback to post screenshot
                            screenshot_bytes = await post.screenshot()
                            ocr_text = extract_text_from_bytes(screenshot_bytes)
                        finally:
                            await img_page.close()
                    else:
                        screenshot_bytes = await post.screenshot()
                        ocr_text = extract_text_from_bytes(screenshot_bytes)

                    # 3. Get the 'alt' text
                    
                    # 4. Get the 'alt' text
                    alt_text = await img_el.get_attribute("alt") if img_el else ""
                    
                    combined_text = f"{alt_text} {ocr_text}".strip()
                    if not combined_text:
                        continue
                        
                    logger.info(f"Post {i+1} OCR combined text: \n--- START ---\n{combined_text}\n--- END ---")
                    
                    date_obj, time_obj = parse_date(combined_text)
                    if not date_obj:
                        logger.info(f"Post {i+1} skipped: No date detected.")
                        continue

                    # 5. Extract Title and Clean it up
                    lines = [line.strip() for line in combined_text.split("\n") if line.strip()]
                    title = lines[0][:200] if lines else f"Event @ {profile_name}"
                    
                    # If first line is too long, it's probably a description, not a title
                    if len(title) > 80:
                         # Try to find a line that looks more like a title (e.g. contains names or venue)
                         found_title = False
                         for line in lines:
                             if profile_name.lower() in line.lower() or "pres." in line.lower() or "at " in line.lower():
                                 title = line[:200]
                                 found_title = True
                                 break
                         if not found_title:
                             title = title[:80] + "..."

                    # OCR Fixes for Crobar
                    p_lower = profile_name.lower()
                    if "crooar" in title.lower() or "crobar" in title.lower() or p_lower in title.lower():
                        title = title.replace("crooar", "Crobar").replace("crobar", "Crobar")
                        # If title is generic, try harder
                        if len(title.strip()) <= 10 or "Crobar" == title.strip():
                             for line in lines[1:5]:
                                 if len(line) > 5:
                                     title = f"Crobar: {line}"
                                     break
                                
                    title_norm = normalize_title(title)
                    dedupe = make_hash(title_norm, date_obj.isoformat(), profile_name)

                    existing = db.query(Event).filter_by(dedupe_hash=dedupe).first()
                    if existing:
                        # Update image if missing
                        if (not existing.media_url or "images.unsplash.com" in existing.media_url) and media_url:
                            existing.media_url = media_url
                            db.commit()
                            logger.info(f"Updated image for existing event: {existing.title}")
                        continue

                    genres, artists = detect_genres(combined_text, hints=[title, profile_name])
                    
                    # Get post link
                    link = "https://www.instagram.com"
                    href = await post.get_attribute("href")
                    if not href:
                        parent = await post.query_selector("xpath=..")
                        if parent:
                            href = await parent.get_attribute("href")
                    
                    if href:
                         if href.startswith("http"):
                             link = href
                         else:
                             link = f"https://www.instagram.com{href}"

                    ev = Event(
                        title=title,
                        title_norm=title_norm,
                        date=date_obj,
                        time=time_obj,
                        venue=profile_name,
                        genres=genres,
                        source_type="instagram",
                        source_name=profile_name,
                        source_link=link,
                        media_url=media_url, 
                        dedupe_hash=dedupe,
                        status="published" if force_publish else "queued",
                    )
                    db.add(ev)
                    db.flush()
                    created += 1
                    logger.info(f"✅ Added event: {title} on {date_obj}")
                    
                except Exception as e:
                    logger.error(f"Error processing post {i} from {profile_name}: {e}")
                    
            db.commit()
        finally:
            db.close()
            
        return created

    except Exception as e:
        logger.error(f"Error scraping profile {profile_name}: {e}")
        return 0
    finally:
        await page.close()

async def run(limit=5, force_publish=False):
    profiles = (os.getenv("INSTAGRAM_PROFILES") or "").split(",")
    profiles = [p.strip() for p in profiles if p.strip()]
    if not profiles:
        logger.warning("No INSTAGRAM_PROFILES set in .env")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Use a real user agent to decrease blocking risk
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        total_created = 0
        for profile in profiles:
            created = await scrape_profile(context, profile, limit=limit, force_publish=force_publish)
            total_created += created
            
        await browser.close()
        logger.info(f"Playwright Instagram scraper finished. Total added: {total_created}")

if __name__ == "__main__":
    asyncio.run(run())
