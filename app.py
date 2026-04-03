import validators
import streamlit as st

from urllib.parse import urlparse, parse_qs

from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain_groq import ChatGroq
from langchain_community.document_loaders import UnstructuredURLLoader

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
You are a helpful summarization assistant.

Summarize the following content clearly and concisely in about 400-700 words.
Highlight:
- the main topic
- key points
- important takeaways
- any conclusion or final message

Content:
{text}
"""

prompt = PromptTemplate(
    template=PROMPT_TEMPLATE,
    input_variables=["text"]
)


# ------------------- HELPERS -------------------
def extract_video_id(url: str) -> str | None:
    """Extract YouTube video ID from URL."""
    parsed = urlparse(url)

    if parsed.hostname in ["www.youtube.com", "youtube.com", "m.youtube.com"]:
        return parse_qs(parsed.query).get("v", [None])[0]
    elif parsed.hostname == "youtu.be":
        return parsed.path.lstrip("/")

    return None


def get_youtube_text(youtube_url: str) -> str:
    """Fetch transcript; if unavailable, fall back to title + description."""
    video_id = extract_video_id(youtube_url)
    if not video_id:
        raise ValueError("Invalid YouTube URL")

    # Try transcript first
    try:
        transcript = YouTubeTranscriptApi().fetch(video_id)

        parts = []
        for item in transcript:
            if isinstance(item, dict):
                parts.append(item.get("text", ""))
            else:
                parts.append(getattr(item, "text", ""))

        text = " ".join(part for part in parts if part).strip()
        if text:
            return text
    except Exception:
        pass

    # Fallback to pytubefix
    try:
        yt = YouTubeFix(youtube_url)
        title = yt.title or ""
        description = yt.description or ""
        fallback_text = f"{title}\n\n{description}".strip()

        if not fallback_text:
            raise RuntimeError("No transcript or metadata available.")

        return fallback_text
    except Exception as ex:
        raise RuntimeError(f"Unable to fetch YouTube content: {ex}") from ex


def load_content_from_url(url: str) -> list[Document]:
    """Load text content from a webpage or YouTube video."""
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


def summarize_docs(docs: list[Document], groq_api_key: str) -> str:
    """Summarize documents using modern LangChain runnable style."""
    if not docs:
        raise ValueError("No documents found to summarize.")

    full_text = "\n\n".join(doc.page_content for doc in docs if doc.page_content).strip()
    if not full_text:
        raise ValueError("The extracted content is empty.")

    llm = ChatGroq(
        groq_api_key=groq_api_key,
        model_name="openai/gpt-oss-120b",
    )

    chain = prompt | llm

    response = chain.invoke({"text": full_text})

    # AIMessage -> string
    return getattr(response, "content", str(response))


# ------------------- MAIN ACTION -------------------
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
                docs = load_content_from_url(generic_url)
                summary = summarize_docs(docs, groq_api_key)
                st.success("Summary generated successfully.")
                st.write(summary)

        except Exception as e:
            st.exception(e)
