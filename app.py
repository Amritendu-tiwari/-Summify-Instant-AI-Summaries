import validators
import streamlit as st

from urllib.parse import urlparse, parse_qs

from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain.chains.summarize import load_summarize_chain
from langchain_community.document_loaders import UnstructuredURLLoader
from langchain_core.documents import Document

from youtube_transcript_api import YouTubeTranscriptApi
from pytubefix import YouTube as YouTubeFix


# ------------------- STREAMLIT UI -------------------
st.set_page_config(page_title="Summify: Instant AI Summaries", page_icon="🦜")
st.title("✨ Summify: Instant AI Summaries")
st.subheader("Summarize a Website or YouTube Video")

with st.sidebar:
    groq_api_key = st.text_input("Enter your Groq API key:", value="", type="password")

generic_url = st.text_input("URL", placeholder="Paste a website or YouTube link")


# ------------------- PROMPT -------------------
PROMPT_TEMPLATE = """
Provide a clear and concise summary of the following content in about 300-500 words.
Highlight the key points and important takeaways.

Content:
{text}
"""

prompt = PromptTemplate(template=PROMPT_TEMPLATE, input_variables=["text"])


# ------------------- FUNCTIONS -------------------
def extract_video_id(url: str) -> str | None:
    """Extract YouTube video ID from a URL."""
    parsed = urlparse(url)

    if parsed.hostname in ["www.youtube.com", "youtube.com", "m.youtube.com"]:
        return parse_qs(parsed.query).get("v", [None])[0]

    if parsed.hostname == "youtu.be":
        return parsed.path.lstrip("/")

    return None


def get_youtube_text(youtube_url: str) -> str:
    """
    Try transcript first.
    If transcript is unavailable, fall back to title + description.
    """
    video_id = extract_video_id(youtube_url)
    if not video_id:
        raise ValueError("Invalid YouTube URL")

    # youtube-transcript-api supports fetch(video_id)
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(video_id)
        text_parts = []

        for item in transcript:
            if isinstance(item, dict):
                text_parts.append(item.get("text", ""))
            else:
                text_parts.append(getattr(item, "text", ""))

        full_text = " ".join(part for part in text_parts if part).strip()
        if full_text:
            return full_text

    except Exception:
        pass

    try:
        yt = YouTubeFix(youtube_url)
        title = yt.title or "YouTube Video"
        description = yt.description or ""
        combined = f"{title}\n\n{description}".strip()

        if not combined:
            raise RuntimeError("No transcript, title, or description available.")

        return combined

    except Exception as ex:
        raise RuntimeError(f"Unable to fetch YouTube content: {ex}") from ex


def load_content_from_url(url: str):
    """Load content from either YouTube or a regular webpage."""
    if "youtube.com" in url or "youtu.be" in url:
        text = get_youtube_text(url)
        return [Document(page_content=text)]

    loader = UnstructuredURLLoader(
        urls=[url],
        ssl_verify=False,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        },
    )
    return loader.load()


# ------------------- SUMMARIZATION -------------------
if st.button("Summarize the Content"):
    if not groq_api_key.strip():
        st.error("Please enter your Groq API key.")
    elif not generic_url.strip():
        st.error("Please enter a URL.")
    elif not validators.url(generic_url):
        st.error("Please enter a valid URL.")
    else:
        try:
            with st.spinner("Fetching and summarizing..."):
                llm = ChatGroq(
                    groq_api_key=groq_api_key,
                    model_name="openai/gpt-oss-120b",
                )

                docs = load_content_from_url(generic_url)

                if not docs:
                    st.error("No content could be extracted from the URL.")
                else:
                    chain = load_summarize_chain(
                        llm=llm,
                        chain_type="stuff",
                        prompt=prompt,
                        verbose=False,
                    )

                    summary = chain.invoke(docs)
                    if isinstance(summary, dict) and "output_text" in summary:
                        st.success(summary["output_text"])
                    else:
                        st.success(str(summary))

        except Exception as e:
            st.exception(e)
