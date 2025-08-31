import validators, streamlit as st
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain.chains.summarize import load_summarize_chain
from langchain_community.document_loaders import UnstructuredURLLoader
from langchain.schema import Document
from youtube_transcript_api import YouTubeTranscriptApi
from pytubefix import YouTube as YouTubeFix
from urllib.parse import urlparse, parse_qs


# ------------------- STREAMLIT UI -------------------
st.set_page_config(page_title="Summify: Instant AI Summaries", page_icon="🦜")
st.title("✨ Summify: Instant AI Summaries")
st.subheader("Summarize a Website or YouTube Video")


# ------------------- SIDEBAR -------------------
with st.sidebar:
    groq_api_key = st.text_input("Enter your Groq API key:", value="", type="password")


generic_url = st.text_input("URL", label_visibility="collapsed")


# ------------------- LLM -------------------
llm = ChatGroq(groq_api_key=groq_api_key, model_name="openai/gpt-oss-120b")

Prompt_template = """
Provide a clear and concise summary of the following content in about 1000 words. 
Highlight the key points and important takeaways.

Content: {text}
"""
prompt = PromptTemplate(template=Prompt_template, input_variables=["text"])

# ------------------- FUNCTIONS -------------------
def extract_video_id(url: str) -> str:
    """Extract YouTube video ID from URL."""
    parsed = urlparse(url)
    if parsed.hostname in ["www.youtube.com", "youtube.com"]:
        return parse_qs(parsed.query).get("v", [None])[0]
    elif parsed.hostname == "youtu.be":
        return parsed.path.lstrip("/")
    return None


def get_youtube_text(youtube_url: str) -> str:
    """Try fetching transcript, else fallback to pytubefix for title/description."""
    video_id = extract_video_id(youtube_url)
    if not video_id:
        raise ValueError("Invalid YouTube URL")

    # Try transcript
    try:
        transcript_list = YouTubeTranscriptApi().fetch(video_id)
        return " ".join([t["text"] for t in transcript_list])
    except Exception as e:
        print("")

        try:
            yt = YouTubeFix(youtube_url)
            description = yt.description or ""
            return yt.title + "\n\n" + description
        except Exception as ex:
            raise RuntimeError(f"Unable to fetch YouTube content: {ex}")


# ------------------- SUMMARIZATION -------------------
if st.button("Summarize the Content"):
    if not groq_api_key.strip() or not generic_url.strip():
        st.error("Please provide all required inputs.")
    elif not validators.url(generic_url):
        st.error("Please enter a valid URL.")
    else:
        try:
            with st.spinner("Fetching and summarizing..."):
                if "youtube.com" in generic_url or "youtu.be" in generic_url:
                    text = get_youtube_text(generic_url)
                    docs = [Document(page_content=text)]
                else:
                    loader = UnstructuredURLLoader(
                        urls=[generic_url],
                        ssl_verify=False,
                        headers={
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                                          "Chrome/58.0.3029.110 Safari/537.36"
                        }
                    )
                    docs = loader.load()

                chain = load_summarize_chain(llm, chain_type="stuff", prompt=prompt, verbose=True)
                summary = chain.run(docs)

                st.success(summary)

        except Exception as e:
            st.exception(e)



