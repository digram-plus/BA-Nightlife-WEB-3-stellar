--
-- PostgreSQL database dump
--

\restrict M6t7LCEremLcRfx9MnI5MadSQA6GCUVSOa12rdkcW5Rb7oY1k9yZ7nOigddgUnp

-- Dumped from database version 16.10 (Debian 16.10-1.pgdg13+1)
-- Dumped by pg_dump version 16.10 (Debian 16.10-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: events; Type: TABLE; Schema: public; Owner: ba
--

CREATE TABLE public.events (
    id integer NOT NULL,
    title character varying(255) NOT NULL,
    event_date date NOT NULL,
    start_time time without time zone,
    end_time time without time zone,
    artist character varying(255),
    venue character varying(255),
    city character varying(120),
    genre character varying(64),
    price_min double precision,
    price_max double precision,
    source_url text,
    image_url text,
    is_canceled boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    status character varying(32) DEFAULT 'queued'::character varying,
    published_msg_id bigint,
    published_topic_id bigint,
    genres text[]
);


ALTER TABLE public.events OWNER TO ba;

--
-- Name: events_id_seq; Type: SEQUENCE; Schema: public; Owner: ba
--

CREATE SEQUENCE public.events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.events_id_seq OWNER TO ba;

--
-- Name: events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: ba
--

ALTER SEQUENCE public.events_id_seq OWNED BY public.events.id;


--
-- Name: events id; Type: DEFAULT; Schema: public; Owner: ba
--

ALTER TABLE ONLY public.events ALTER COLUMN id SET DEFAULT nextval('public.events_id_seq'::regclass);


--
-- Data for Name: events; Type: TABLE DATA; Schema: public; Owner: ba
--

COPY public.events (id, title, event_date, start_time, end_time, artist, venue, city, genre, price_min, price_max, source_url, image_url, is_canceled, created_at, updated_at, status, published_msg_id, published_topic_id, genres) FROM stdin;
3	Test Jazz Event	2025-10-11	21:00:00	\N	Blue Note Trio	Thelonious Club	Buenos Aires	jazz	\N	\N	https://theloniousclub.com.ar/	https://theloniousclub.com.ar/wp-content/uploads/2024/12/jazz-night.jpg	f	2025-10-10 19:32:37.127194+00	2025-10-16 11:24:47.27759+00	skipped	29	27	{jazz}
\.


--
-- Name: events_id_seq; Type: SEQUENCE SET; Schema: public; Owner: ba
--

SELECT pg_catalog.setval('public.events_id_seq', 3, true);


--
-- Name: events events_pkey; Type: CONSTRAINT; Schema: public; Owner: ba
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_pkey PRIMARY KEY (id);


--
-- Name: ix_events_genre; Type: INDEX; Schema: public; Owner: ba
--

CREATE INDEX ix_events_genre ON public.events USING btree (genre);


--
-- PostgreSQL database dump complete
--

\unrestrict M6t7LCEremLcRfx9MnI5MadSQA6GCUVSOa12rdkcW5Rb7oY1k9yZ7nOigddgUnp

