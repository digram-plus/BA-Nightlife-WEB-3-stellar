/**
 * --------------------------------------------------------------------------
 * Library Home Passline (v1.0.0): home
 * created nov 2023 Raúl Urrea C. / rurrea@passline.dev
 * HOME SLIDER
 * MARQUEE 
 * SEARCH
 * LOAD FULL HOME
 * --------------------------------------------------------------------------
 */


let eventTop;
let billboardByCountry;
let slidersHome;
let venuessHome;

const loadEvent = document.querySelector('#callEvents');
const textLoad = loadEvent.innerHTML;
const firstListEvent = document.querySelector("#firstListEvent");
const secondListEvent = document.querySelector("#secondListEvent");


let intCont = 0;
let init = 24;
let limit = 24;
let increment = 24;

const myHeaders = new Headers();
const raw = JSON.stringify({
  "country": country,
  "limit": "0,48"
});

const requestOptions = {
  method: "POST",
  body: raw,
};

const slidersDescktop = [];
const slidersMobile = [];
const bannerHome = [];

fetch("https://api.passline.com/v1/event/GetCountryByBillboardHome", requestOptions)
  .then((response) => response.json())
  .then((result) => {

    eventTop = result.EventTop10;
    billboardByCountry = result.BillboardByCountry;
    slidersHome = result.Sliders;
    venuessHome = result.VenuesBanner;



  
    if (Array.isArray(slidersHome)) {
      const items = slidersHome.map((item, index) => ({
        item_id: item.evento || "",
        item_name: item.slug_evento || "",
        item_category: "",
        price: 0,
        index: index + 1,
        event_date: "",
        location: "",
        affiliation: "Passline"
      }));

      dataLayer.push({
        event: "view_item_list",
        ecommerce: {
          item_list_id: "hero",
          item_list_name: "Hero",
          items: items
        }
      });
    }


    if (Array.isArray(eventTop)) {
      const items = eventTop.map((item, index) => ({
                item_id: item.id || "",
                item_name: item.nombre || "",
                item_category: "",
                price: 0,
                index: index + 1,
                event_date: item.fecha_inicio	|| "",
                location: item.lugar || "",
                affiliation: "Passline"
      }));

      dataLayer.push({
        event: "view_item_list",
        ecommerce: {
          item_list_id: "slider",
          item_list_name: "Slider",
          items: items
        }
      });
    }

    
    if (Array.isArray(billboardByCountry)) {
      const items = billboardByCountry.map((item, index) => ({
                item_id: item.id || "",
                item_name: item.nombre || "",
                item_category: item.category_name || "",
                price: item.precio_min || 0,
                index: index + 1,
                event_date: item.fecha_inicio	|| "",
                location: item.lugar || "",
                affiliation: "Passline"
      }));

      dataLayer.push({
        event: "view_item_list",
        ecommerce: {
          item_list_id: "lista_principal",
          item_list_name: "Lista principal",
          items: items
        }
      });
    }


    


    slidersHome.forEach(element => {

        const _type = element.type;

        if(_type=="desktop"){
            slidersDescktop.push(element);
        }

        if(_type=="mobile"){
            slidersMobile.push(element);
        }

        if(_type=="mini_banners"){
            bannerHome.push(element);
        }

        

        
    });

    //console.log(slidersDescktop);
    //console.log(slidersMobile);
    //console.log(bannerHome);


    fetchSlider(slidersDescktop,slidersMobile,0,5);
    

    
   
    

    if(bannerHome.length>0){
        shuffleArray(bannerHome);
        getBannerContents(bannerHome);
    }
    
    if(venuessHome.length>5){
      document.getElementById("venues-container").style.display = "";
      venueslist(venuessHome);
    }


    startMarquee('.marquee',0.15,eventTop);


    callEventsHome(firstListEvent,billboardByCountry,textLoad,1);

  
    
    function handleScroll() {
      const objetivo = secondListEvent;
      const rect = objetivo.getBoundingClientRect();
      const windowHeight = (window.innerHeight || document.documentElement.clientHeight);
    
      // Comprobar si el div está en la vista
      if (rect.top <= windowHeight && rect.bottom >= 0) {
        callEventsHome(secondListEvent,billboardByCountry,textLoad,2);
          // Elimina el listener si solo quieres que se ejecute una vez
          document.removeEventListener("scroll", handleScroll);
      }
    }
    
    document.addEventListener("scroll", handleScroll);




   

    const listEvent = document.querySelector("#listloadresult");
    //callEvents(init+=increment,limit,listEvent,textLoad);

    loadEvent.addEventListener('click',()=>{
      loadEvent.innerHTML = "<img src='assets/img/inkling_spinner.gif' alt='-' style='width: 35px;margin: 0px 70px;'>";   
      
      callEvents(init+=increment,limit,listEvent,textLoad);
    });

  })
  .catch((error) => {});

 

//Función venues list
function venueslist(venues){

         if (venues && venues.length > 0) {
            
            // Creamos la estructura
            const section = document.createElement('div');
            section.className = 'position-relative';

            
            const container = document.createElement('div');
            container.className = 'overflow-hidden';

            const bcarrusel = document.createElement('div');
            bcarrusel.className = 'd-flex transition';
            bcarrusel.style = "gap: 0.52rem;";
            bcarrusel.id = "brandCarousel";
          
            // Recorrer cada venue
            venues.forEach(venue => {
                
                const a = document.createElement('a');
                a.className = 'brand-item btn btn-dark d-flex';
                a.href = venue.link;
                a.target = '_blank'; // Opcional: abre en nueva pestaña

                const img = document.createElement('img');
                img.src = venue.url_banner_image;
                img.className = 'w-100 my-auto';
                img.alt = venue.nombre; // Mejor para SEO

                a.appendChild(img);
                bcarrusel.appendChild(a);
            });

            // Armar todo
            container.appendChild(bcarrusel);

            section.appendChild(container);

            const prediv = document.createElement('div');
            prediv.className = 'position-absolute top-50 start-0 translate-middle';
            const prevBtndiv = document.createElement('button');
            prevBtndiv.className = 'btn btn-link';
            prevBtndiv.id = 'prevBtnArrowBrand';
            prevBtndiv.style = 'margin-left: -26px;padding: 4px 10px;border-radius: 20px;';
            prevBtndiv.innerHTML = '<i class="bi bi-chevron-left fs-6 fw-bold"></i>';
            prediv.appendChild(prevBtndiv);

            const nextdiv = document.createElement('div');
            nextdiv.className = 'position-absolute top-50 end-0 translate-middle';
            const nextBtndiv = document.createElement('button');
            nextBtndiv.className = 'btn btn-link';
            nextBtndiv.id = 'nextBtnArrowBrand';
            nextBtndiv.style = 'margin-right: -29px;padding: 4px 10px;border-radius: 20px;';
            nextBtndiv.innerHTML = '<i class="bi bi-chevron-right fs-6 fw-bold"></i>';
            nextdiv.appendChild(nextBtndiv);

            section.appendChild(prediv);
            section.appendChild(nextdiv);

            // Insertar en el contenedor que tengas en tu HTML
            document.getElementById('venues-container').appendChild(section);
            //document.getElementById('venues-container').appendChild(prediv);
            //document.getElementById('venues-container').appendChild(nextdiv);


            startvenues();

  
          
          }
  
}


function startvenues(){

  const carousel = document.getElementById('brandCarousel');
  const items = carousel.querySelectorAll('.brand-item');
  const prevBtn = document.getElementById('prevBtnArrowBrand');
  const nextBtn = document.getElementById('nextBtnArrowBrand');

  let position = 0;
  const itemCount = items.length;
  const gap = 8; // 0.5rem en px
  let visibleCount = window.innerWidth >= 768 ? 6 : 2;
  let autoPlayInterval;

  function updateVisibleCount() {
    visibleCount = window.innerWidth >= 768 ? 6 : 2;
  }

  function move(direction) {
    updateVisibleCount();

    if (direction === 'next') {
      position = (position + 1) % itemCount;
    } else if (direction === 'prev') {
      position = (position - 1 + itemCount) % itemCount;
    }

    const translateX = -position * (carousel.querySelector('.brand-item').offsetWidth + gap);
    carousel.style.transform = `translateX(${translateX}px)`;
  }

  // Acción al hacer clic en las flechas
  nextBtn.addEventListener('click', () => move('next'));
  prevBtn.addEventListener('click', () => move('prev'));

  // Auto-reproducción cada 5 segundos
  function startAutoPlay() {
    autoPlayInterval = setInterval(() => {
      move('next');
    }, 5000); // Cambiar a tu intervalo deseado (en milisegundos)
  }

  // Detener la auto-reproducción al hacer clic en una flecha
  nextBtn.addEventListener('click', () => clearInterval(autoPlayInterval));
  prevBtn.addEventListener('click', () => clearInterval(autoPlayInterval));

  // Empezar la auto-reproducción al cargar la página
  window.addEventListener('load', startAutoPlay);

  // Cambiar el tamaño visible al redimensionar la ventana
  window.addEventListener('resize', () => {
    updateVisibleCount();
    move(); // recalcular posición
  });

}

// Función para mezclar aleatoriamente un array
function shuffleArray(array) {
  for (let i = array.length - 1; i > 0; i--) {
      const randomIndex = Math.floor(Math.random() * (i + 1));
      [array[i], array[randomIndex]] = [array[randomIndex], array[i]]; // Intercambia los elementos
  }
}


//import { upPosicionScroll } from "../modules/home/resizescroll.js"; //modulo para manejar tamaños de secciones
// Función para actualizar la posición del scroll
function actualizarPosicionScroll() {
    let posicion = window.scrollY || window.pageYOffset;
    let section = document.getElementById("section-one");
    let element = document.getElementById("search-container");

    if(posicion > 585){
        element.classList.add("static");
        section.style.padding = "85px 0 0 0";
    }else{
        element.classList.remove("static");
        if(section){
            section.style.padding = "0 0 0 0";
        }
        
    }
}
// Registra un controlador de eventos para el evento 'scroll'
window.addEventListener("scroll", actualizarPosicionScroll);

// Llama a la función para mostrar la posición inicial
function upPosicionScroll() {
    actualizarPosicionScroll();
}





//import { getSliderContents } from "../modules/home/slider2.js"; 
//*************** HOME SLIDER START */    
//Contenedor slider descktop
const slideContainer = document.querySelector('.slider-container');
const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');
const imageWidth = (slideContainer.dataset.width)? slideContainer.dataset.width : 1920;
const imageHeight = (slideContainer.dataset.height)? slideContainer.dataset.height : 600;

//Contenedor slider descktop
const slideContainerM = document.querySelector('.slider-container-mobile');
const prevBtnM = document.getElementById('prevBtnM');
const nextBtnM = document.getElementById('nextBtnM');
const imageWidthM = (slideContainerM.dataset.width)? slideContainerM.dataset.width : 800;
const imageHeightM = (slideContainerM.dataset.height)? slideContainerM.dataset.height : 380;

//Loading descktop - mobile
const loadingSlide = document.querySelector(".loading-slide");
const loadingSlideM = document.querySelector(".loading-slide-mobile");

let slides;
let slidesM;
let currentIndex = 0; // Variable para almacenar el posicion del intervalo  
let intervalId; // Variable para almacenar el ID del intervalo  
let currentIndexM = 0; // Variable para almacenar el posicion del intervalo  
let intervalIdM; // Variable para almacenar el ID del intervalo  
let intervalTime = 6000; // Variable para tiempo  del intervalo  
let initSliderInterval = setTimeout(reloadJ, intervalTime);


function reloadJ(){
  intervalId = setInterval(nextSlide, 6000);
  intervalIdM = setInterval(nextSlideM, 6000);
  

  fetchSlider(slidersDescktop,slidersMobile,5,30);
  
  clearInterval(initSliderInterval);
  initSliderInterval = null;
}

async function fetchSlider(sDescktop,sMobile,init,limit) {

  
  let itemsDescktop = sDescktop; 
  let itemsMobile = sMobile; 

       if (itemsDescktop && itemsMobile) {

          let cont = init;
          let contM = init;
          
          //itemsDescktop.forEach(element => {

          for (let index = cont; index < limit; index++) {
            
            let element = itemsDescktop[index];

            if(element){
            
            let _titulo = element.titulo;
            let _imagen = element.imagen;
            let _enlace = element.enlace;
            let _target = element.target;
            let _slug = element.slug_evento;
            let _type = element.type;

           // if(cont<=5){
              // Estructura a crear cada item slider <div><a><img></a></div>
              // Creamos elemento (div.slide) slide para el slider con su enlace e imagen (agregamos clase active para el primer item)
              const divElement = document.createElement('div');
              (cont==0)? divElement.className = "slide active" :  divElement.className = "slide";
              cont++;
              // Crear el elemento <a> (enlace)
              let linkElement = document.createElement('a');
              linkElement.href = _enlace;
              linkElement.target = _target;
              linkElement.className = "event-slider-passline";
              linkElement.dataset.itemid = element.evento;
              linkElement.dataset.itemname = element.slug_evento;
              linkElement.dataset.price = 0;
              linkElement.dataset.index = "";
              linkElement.dataset.dataLocation = "";
              linkElement.dataset.eventdata = "";
              linkElement.dataset.category = "";
              linkElement.dataset.trackingAttached = index;
              // Crear el elemento <img> (imagen)
              let imgElement = document.createElement('img');
              imgElement.src = _imagen; // Establece la ruta de la imagen
              imgElement.setAttribute("alt",_titulo);
              imgElement.setAttribute("title",_titulo);
              imgElement.width = 1920;
              imgElement.height= 600;
             // imgElement.loading = 'lazy';
              imgElement.className = "d-none d-sm-block w-100";
              // Agregar la imagen como hijo del enlace
              linkElement.appendChild(imgElement);
              // Agregar el enlace como hijo del div
              divElement.appendChild(linkElement);
              // Agregar el item div como hijo del Contenedor del slider
              slideContainer.appendChild(divElement);
              
          //  }

            }
          }
            
         // });

         

         // itemsMobile.forEach(element => {

         for (let index = contM; index < limit; index++) {

            let element = itemsMobile[index];

            if(element){

            let _titulo = element.titulo;
            let _imagen = element.imagen;
            let _enlace = element.enlace;
            let _target = element.target;
            let _slug = element.slug_evento;
            let _type = element.type;

       
           // if(contM<=5){
            let divElement = document.createElement('div');
              (contM==0)? divElement.className = "slide-mobile active" :  divElement.className = "slide-mobile";
              contM++;
              // Crear el elemento <a> (enlace)
              let linkElement = document.createElement('a');
              linkElement.href = _enlace;
              linkElement.target = _target;
              linkElement.className = "event-slider-passline";
              linkElement.dataset.itemid = element.evento;
              linkElement.dataset.itemname = element.slug_evento;
              linkElement.dataset.price = 0;
              linkElement.dataset.index = "";
              linkElement.dataset.dataLocation = "";
              linkElement.dataset.eventdata = "";
              linkElement.dataset.category = "";
              linkElement.dataset.trackingAttached = index;
              // Crear el elemento <img> (imagen)
              let imgElement = document.createElement('img');
              imgElement.src = _imagen; // Establece la ruta de la imagen
              imgElement.setAttribute("alt",_titulo);
              imgElement.setAttribute("title",_titulo);
              imgElement.width = 800;
              imgElement.height= 380;
              //imgElement.loading = 'lazy';
              imgElement.className = "d-block d-sm-none w-100";
              // Agregar la imagen como hijo del enlace
              linkElement.appendChild(imgElement);
              // Agregar el enlace como hijo del div
              divElement.appendChild(linkElement);
              // Agregar el item div como hijo del Contenedor del slider
              slideContainerM.appendChild(divElement);
           // }
            }

         }
            
          //});





         
          slides = document.querySelectorAll('.slide');
          slidesM = document.querySelectorAll('.slide-mobile');
          showSlide(currentIndex);
          showSlideM(currentIndexM);
          
          ocultarIndicadorDeCarga(loadingSlide);
          ocultarIndicadorDeCarga(loadingSlideM);

        } else {
            slideContainer.remove();
        }
 
} 


 
function ajustarAnchoElemento() {
        const anchoPantalla = window.innerWidth;
        const altoPantalla = window.innerHeight;
        // Puedes ajustar los valores de escala según tus necesidades
        const escalaAncho = anchoPantalla / imageWidth; // Ancho original de la imagen
        const escalaAlto = altoPantalla / imageHeight;  // Alto original de la imagen

        const escala = Math.min(escalaAncho, escalaAlto);

        const escalaAnchoM = anchoPantalla / imageWidthM; // Ancho original de la imagen
        const escalaAltoM = altoPantalla / imageHeightM;  // Alto original de la imagen

        const escalaM = Math.min(escalaAnchoM, escalaAltoM);

        slideContainer.style.height = parseInt((escala * imageHeight)-3) + 'px'; 
        slideContainerM.style.height = parseInt((escalaM * imageHeightM)-3) + 'px'; 
        loadingSlide.style.height = (escala * imageHeight) + 'px';
        loadingSlideM.style.height = (escalaM * imageHeightM) + 'px';
}
// Llama a la función inicialmente para establecer el ancho al cargar la página
ajustarAnchoElemento();


// Agrega un evento de cambio de tamaño de pantalla
window.addEventListener('resize', ajustarAnchoElemento);


function showSlide(index) {
  slides.forEach((slide, i) => {
      if (i === index) {
          slide.classList.add('active');
      } else {
          slide.classList.remove('active');
      }
  });
} 

function showSlideM(indexM) {
  slidesM.forEach((slideM, i) => {
      if (i === indexM) {
        slideM.classList.add('active');
      } else {
        slideM.classList.remove('active');
      }
  });
} 


nextBtn.addEventListener('click', () => {
  nextSlide();
});
prevBtn.addEventListener('click', () => {
  prevSlide();
});

function nextSlide() {
  clearInterval(intervalId);
  intervalId = null;

  currentIndex = (currentIndex + 1) % slides.length;
  showSlide(currentIndex);

  intervalId = setInterval(nextSlide, 6000); 
}

function prevSlide() {
  clearInterval(intervalId);
  intervalId = null;

  currentIndex = (currentIndex -1) % slides.length;
  if(currentIndex<0){ currentIndex = slides.length-1; }
  showSlide(currentIndex);

  intervalId = setInterval(nextSlide, 6000); 
}

nextBtnM.addEventListener('click', () => {
  nextSlideM();
});
prevBtnM.addEventListener('click', () => {
  prevSlideM();
});

function nextSlideM() {
  clearInterval(intervalIdM);
  intervalIdM = null;
  
  currentIndexM = (currentIndexM + 1) % slidesM.length;
  showSlideM(currentIndexM);

  intervalIdM = setInterval(nextSlideM, 6000); 
}

function prevSlideM() {
  clearInterval(intervalIdM);
  intervalIdM = null;

  currentIndexM = (currentIndexM -1) % slidesM.length;
  if(currentIndexM<0){ currentIndexM = slidesM.length-1; }
  showSlideM(currentIndexM);

  intervalIdM = setInterval(nextSlideM, 6000); 
}


 
function ocultarIndicadorDeCarga(element) {
  // Oculta el indicador de carga una vez que la solicitud se haya completado
  element.style.opacity = 0;
  element.style.zIndex = 0;
}  

function mostrarError(error,mensajeError,element) {
    // Muestra un mensaje de error en la interfaz de usuario
    element.innerHTML = mensajeError+": "+error;
}
//*************** HOME SLIDER END */




//import { getBannerContents } from "../modules/home/minibanner2.js";
//*************** HOME BANNER START */    
//Contenedor BANNER descktop
const first_minibanner = document.querySelector('#first_minibanner');
const second_minibanner = document.querySelector('#second_minibanner');

async function fetchBanner(slidersHome) {


  let items = slidersHome;

      if (items) {
          let cont = 0;
          items.forEach(element => {

            const _imagen = element.imagen;
            const _enlace = element.enlace;
            const _target = element.target;
            const _type = element.type;

            if(_type=="mini_banners"){


                const child = document.createElement("div");
                if(cont>0){ var mhide = 'd-none d-sm-block' }else{ var mhide = '';}

                child.className = "col-12 col-sm-4 my-2 "+mhide;
            
                let elenlace = _enlace;  
                if(_enlace==""){ elenlace = "https://www.passline.com"; }
                   
                    let elemtInsert = `<a href="${elenlace}" taget="${_target}" class="banner " aria-label="${elenlace}">
                                            <div class="position-relative">
                                            <img src="${_imagen}" class="w-100 " alt=""/>
                                            </div>
                                        </a>`;
                              
                child.innerHTML =  elemtInsert; 
            
                if(cont<3){
                    first_minibanner.appendChild(child);
                }
              
                 

                cont++;

           
            }

 
            

           

          
            
          });

         
      

          

      } else {
         // console.error('Error al cargar las imágenes desde la API');
      }
 
}


function getBannerContents(slidersHome) {




    fetchBanner(slidersHome);
}  
//*************** HOME BANNER END */








  //after window is completed load
  //1 class selector for marquee
  //2 marquee speed 0.2
function startMarquee(selector, speed, eventTop) {

      let isDragging = false;
      let startX;
      let scrollLeft;

      let querySelector = selector;
      let getSpeed = speed;



  let items = eventTop;
  const parentSelector = document.querySelector(selector); 

 
       if (items) {

              //let firstElement = parentSelector?.children[0];
              //let secondElement = parentSelector?.children[1];
              //let tertiaryElement = parentSelector?.children[2];


              const elementos = document.querySelectorAll('.col-marquee');
              elementos.forEach(elemento => {
               


                let uu = 1;

          
              items.forEach(element => {

                  const _url      = element.url;
                  const _imagen   = element.image;
                  const _slug     = element.slug;

                  
                  // Crear el elemento <a> (enlace)
                  let linkElement = document.createElement('a');
                  linkElement.href = _url;
                  linkElement.className = "event-carousel-passline";
                  linkElement.dataset.itemid = element.id;
                  linkElement.dataset.itemname = element.nombre;
                  linkElement.dataset.price = 0;
                  linkElement.dataset.index = "";
                  linkElement.dataset.dataLocation = element.lugar;
                  linkElement.dataset.eventdata = element.fecha_inicio;
                  linkElement.dataset.category = "";
                  linkElement.dataset.trackingAttached = uu; 

                  const spanElement = document.createElement('span');

                  // Crear el elemento <img> (imagen)
                  let imgElement = document.createElement('img');
                 
               
                    imgElement.src = _imagen; // Establece la ruta de la imagen
                    imgElement.setAttribute("alt",_slug);
                    imgElement.setAttribute("title","");
                    imgElement.classList.add("img-marquee");

                      // Agregar la imagen como hijo del enlace
                      spanElement.appendChild(imgElement);
                      // Agregar el enlace como hijo del div
                      linkElement.appendChild(spanElement);
                      // Agregar el item div como hijo del Contenedor del slider
                     /* firstElement.appendChild(linkElement);   
                      secondElement.appendChild(linkElement); 
                      tertiaryElement.appendChild(linkElement); 
*/
                      elemento.appendChild(linkElement); 

                     
              });

            });
              
            playMarque(selector, speed,isDragging);

          } else {
            // console.error('Error al cargar las imágenes desde la API');
          }  




  }
  
function playMarque(selector,speed,isDragging){
              const parentSelector = document.querySelector(selector); 
              let firstElement = parentSelector?.children[0];
              parentSelector?.addEventListener('mouseover', (event) => { speed = 0; });
              parentSelector?.addEventListener('mouseout', (event) => { speed = 0.15; });

              parentSelector?.addEventListener('mousedown', (e) => {
                  speed = 0;
                  isDragging = true;
                  startX = e.pageX - parentSelector.offsetLeft;
                  scrollLeft = parentSelector.scrollLeft;
                  parentSelector.style.cursor = 'grabbing';
                });


                parentSelector?.addEventListener('mouseleave', () => {
                  isDragging = false;
                  parentSelector.style.cursor = 'grab';
                });
                
                parentSelector?.addEventListener('mouseup', () => {
                  isDragging = false;
                  parentSelector.style.cursor = 'grab';
                });
                
                parentSelector?.addEventListener('mousemove', (e) => {
                  if (!isDragging) return;
                  e.preventDefault();
                  const x = e.pageX - parentSelector.offsetLeft;
                  const walk = (x - startX) * 2; // Ajusta la velocidad de desplazamiento
                  parentSelector.scrollLeft = scrollLeft - walk;
                });  

              
            // const clone = parentSelector?.innerHTML;
              
              
              //parentSelector?.insertAdjacentHTML('beforeend', clone);
             // parentSelector?.insertAdjacentHTML('beforeend', clone);
              
              let i = 0;
              
              setInterval(function () {
              firstElement.style.marginLeft = `-${i}px`;
              if (i > firstElement.clientWidth) {
                  i = 0;
              }
              i = i + speed;
              }, 0);     

              parentSelector.classList.add("off");  
              parentSelector.classList.remove("load-marque-back"); 

}


//import { callEventsHome } from "../modules/event/callEventsHome.js?003";
import { getCard } from "../modules/event/card.js?04122024";

function callEventList(container,billboardByCountry,text,w){  


  let items = billboardByCountry
  const loadEvent = document.querySelector('#callEvents');

  //console.log(items);

  if (items) {
    
   
    if(container.id=="firstListEvent"){ container.innerHTML = ""; }
    if(container.id=="secondListEvent"){ container.innerHTML = ""; }  
          
    let contador = 0;

    items.forEach(element => {

        
            if(w==1 && contador<24){
                //console.log("card:");
                getCard(element,container); 
            }
       
     
            if(w==2 && contador>=24){
                getCard(element,container); 
            }
      

      contador++;

    });

    loadEvent.innerHTML = text;

    } else {
      //  console.error('Error al cargar las imágenes desde la API');
    }


} 


function callEventsHome(container,billboardByCountry,text,w) {
    callEventList(container,billboardByCountry,text,w);
} 




//import { callEvents } from "../modules/event/callEvents.js";
async function callEventListLoad(container,text){  



  const myHeaders = new Headers();
  myHeaders.append("content-type", "application/json");
  myHeaders.append("Accept", "application/json");

  const raw = JSON.stringify({
    "country" : country,
    "limit"   : `${init},${limit}`
  });

  const requestOptions = {
  method: 'POST',
  headers: myHeaders,
  body: raw,
  redirect: 'follow'
  };

  let items;
  const loadEvent = document.querySelector('#callEvents');
  

  try {
  const response = await fetch(`${urlApi}event/GetBillboardByCountry`, requestOptions);
  

  if (response.ok) {

    if(container.id=="firstListEvent"){ container.innerHTML = ""; }
    if(container.id=="secondListEvent"){ container.innerHTML = ""; }  
          
    const data = await response.json();
    items = data;

    items.forEach(element => {
      
     // console.log(element);
      getCard(element,container);

    });

    loadEvent.innerHTML = text;
    if(items.length==0){
      loadEvent.style.display = "none";
    }
    

} else {
  //  console.error('Error al cargar las imágenes desde la API');
}
} catch (error) {
//  console.error('Error al cargar las imágenes desde la API:', error);
} 

} 


function callEvents(initGet,limitGet,container,text) {
    init = initGet;
    limit = limitGet;
    callEventListLoad(container,text);
} 


upPosicionScroll();
getRegions();







//import { getRegions } from "../modules/home/search.js";
let regionSel;

async function cargarComuna(){
   
  const myHeaders = new Headers();
  myHeaders.append("content-type", "application/json");
  myHeaders.append("Accept", "application/json");

  const raw = JSON.stringify({
    "region": regionSel,
    "country": country
  });

  const requestOptions = {
  method: 'POST',
  headers: myHeaders,
  body: raw,
  redirect: 'follow'
  };

  

  let communes;
  const parentSelector = document.querySelector("#comuna"); 
  parentSelector.innerHTML = "";
  const option = document.createElement('option');
  option.value = ""; // Asignar el valor deseado
  option.text = "Loading..."; // Asignar el texto deseado
  parentSelector.appendChild(option);

  try {
        const response = await fetch(`${urlApi}general/GetCommunesByRegion`, requestOptions);
        
          if (response.ok) {

                parentSelector.innerHTML = "";

                const option = document.createElement('option');
                option.value = ""; // Asignar el valor deseado
                option.text = (contact.termino_comuna!="")? contact.termino_comuna : "Por Comuna"; // Asignar el texto deseado
                parentSelector.appendChild(option);

                const data = await response.json();
                communes = data;

                communes.forEach(element => {
                  
                  const option = document.createElement('option');
                  option.value = element.id; // Asignar el valor deseado
                  option.text = convertirEntidadesHtmlAUtf8(element.nombre); // Asignar el texto deseado
                  parentSelector.appendChild(option);

                });


                if(parentSelector.dataset.parent!=""){
                   
                  let valorASeleccionar = parentSelector.dataset.parent;

                  // Recorre las opciones del select
                  for (var i = 0; i < parentSelector.options.length; i++) {
                    let option = parentSelector.options[i];

                    // Si el valor de la opción coincide con el valor que buscas, selecciónala
                    if (option.value === valorASeleccionar) {
                      option.selected = true;
                      break; // Puedes detener el bucle una vez que encuentres la opción
                    }
                  }

                }


            } else {
               console.error('Error 101 al cargar las comunas desde la API');
            }
        } catch (error) {
            console.error('Error 102 al cargar las comunas desde la API:', error); 
        } 

}
async function regiones(){  


      const myHeaders = new Headers();
      myHeaders.append("content-type", "application/json");
      myHeaders.append("Accept", "application/json");
    
      const requestOptions = {
      method: 'GET',
      headers: myHeaders,
      redirect: 'follow'
      };
  
      let regions;
      const parentSelector = document.querySelector("#region"); 
     
   
      parentSelector.addEventListener('change', (e)=> {
        regionSel = parentSelector.value;
        cargarComuna();
      });

      
          try {
            const response = await fetch(`${urlApi}general/GetRegionsByCountry/${country}`, requestOptions);
            if (response.ok) {
  
                    const data = await response.json();
                    regions = data;
  
                    regions.forEach(element => {
                      
                      const option = document.createElement('option');
                      option.value = element.id; // Asignar el valor deseado
                      option.text = convertirEntidadesHtmlAUtf8(element.nombre); // Asignar el texto deseado
                      parentSelector.appendChild(option);
                      
                    });

                    
                    if(parentSelector.dataset.parent!=""){
                       
                        let valorASeleccionar = parentSelector.dataset.parent;

                        // Recorre las opciones del select
                        for (var i = 0; i < parentSelector.options.length; i++) {
                          let option = parentSelector.options[i];

                          // Si el valor de la opción coincide con el valor que buscas, selecciónala
                          if (option.value === valorASeleccionar) {
                            option.selected = true;
                            regionSel = valorASeleccionar;
                            cargarComuna();
                            break; // Puedes detener el bucle una vez que encuentres la opción
                          }
                        }

                    }

                    
                    
  
                } else {
                  //  console.error('Error al cargar las imágenes desde la API');
                }
            } catch (error) {
               // console.error('Error al cargar las imágenes desde la API:', error);
              // alert(error);
            }   
        }


function getRegions() {
    regiones();
} 
