import streamlit as st
import time
from xhtml2pdf import pisa
import markdown
import io
from selenium.webdriver.common.by import By
from seleniumbase import Driver
import pandas as pd


# Function to convert HTML to PDF
def convert_html_to_pdf(html_content):
    pdf = io.BytesIO()
    pisa_status = pisa.CreatePDF(html_content, dest=pdf)
    if pisa_status.err:
        return None
    return pdf.getvalue()


def common_topics(input):
    time.sleep(2)

    from langchain_google_genai import ChatGoogleGenerativeAI

    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        backoff_factor=2,
        verbose=True,
        streaming=True,
        top_k=None,
        top_p=None,
        safety_settings=None,
        google_api_key="AIzaSyD48leSSIcx_chj7nQD75iDWgKeH7IERAg",
        google_cse_id=None,
    )

    from langchain_core.prompts import ChatPromptTemplate

    # Define the prompt template
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """you are a ai assistant, your task is to analyze the course syllabus and provide the common topics list and common topic percentage alone from the course syllabus. Please avoid preamble and conclusion.""",
            ),
            (
                "human",
                "{input}",
            ),
        ]
    )

    chain = prompt | llm
    ai_msg = chain.invoke({"input": input})

    print(f"\n ai msg : {ai_msg.content}")

    return ai_msg.content


def generate_response(data):
    from langchain_google_genai import ChatGoogleGenerativeAI

    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        backoff_factor=2,
        verbose=True,
        streaming=True,
        top_k=None,
        top_p=None,
        safety_settings=None,
        google_api_key="AIzaSyCNDBN9LVR1lUjIMTlAoUr9x_cpe8UsQR4",
        google_cse_id=None,
    )

    from langchain_core.prompts import ChatPromptTemplate

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an educational consultant AI, and your mission is to analyze and compare the syllabus content of multiple courses.
                After comparing, generate a comprehensive syllabus that combines the key topics, ensuring a balanced and 
                integrated curriculum that covers all essential areas. 
                Provide a combined syllabus that integrates the main topics and ensures a cohesive learning experience.""",
            ),
            ("human", "{course}"),
        ]
    )

    chain = prompt | llm
    ai_msg = chain.invoke(
        {
            "course": data,
        }
    )

    return ai_msg.content


# Function to extract syllabus from Udemy course link
def extract_syllabus(udemy_url):
    try:
        from selenium.webdriver.common.by import By
        from seleniumbase import Driver

        driver = Driver(uc=True, headless=False)
        driver.get(udemy_url)

        name = driver.find_element(
            By.CSS_SELECTOR, "h1[data-purpose='lead-title']"
        ).text
        time.sleep(1)

        element = driver.find_element(
            By.CSS_SELECTOR,
            'div[data-purpose="course-curriculum"] button[data-purpose="expand-toggle"].ud-btn.ud-btn-medium.ud-btn-ghost',
        )
        element.click()

        data = {}
        div = driver.find_element(
            By.CSS_SELECTOR, 'div[data-purpose="course-curriculum"]'
        )
        for section in div.find_elements(
            By.CSS_SELECTOR,
            "div.accordion-panel-module--panel--Eb0it.section--panel--qYPjj",
        ):
            title_element = section.find_element(
                By.CSS_SELECTOR, "span.section--section-title--svpHP"
            )
            subdata = []

            for sublinks in section.find_elements(By.CSS_SELECTOR, "span.ud-btn-label"):
                subdata.append(sublinks.text)

            for subtitles in section.find_elements(
                By.CSS_SELECTOR, "span.section--item-title--EWIuI "
            ):
                subdata.append(subtitles.text)

            data[title_element.text] = subdata

        course_data = {"course_title": name, "syllabus": data}
        driver.quit()

        return course_data
    except Exception as e:
        st.error(f"Error extracting syllabus: {e}")
        return {}


# Streamlit app code
st.title("Udemy CourseMate: Syllabus Extractor & Smart Curriculum Generator")

if "course_links" not in st.session_state:
    st.session_state.course_links = ["", ""]


def add_course_link():
    st.session_state.course_links.append("")


def remove_course_link(index):
    if st.session_state.course_links:
        st.session_state.course_links.pop(index)


for i, link in enumerate(st.session_state.course_links):
    col1, col2 = st.columns([8, 2])
    with col1:
        st.session_state.course_links[i] = st.text_input(
            f"Enter Udemy course link {i+1}:", link, key=f"course_link_{i}"
        )
    with col2:
        st.button(
            f"X", key=f"remove_{i}", on_click=lambda idx=i: remove_course_link(idx)
        )

st.button("Add another course link", on_click=add_course_link)

# Button to extract syllabi
if st.button("Generate Syllabus"):
    if st.session_state.course_links:
        with st.spinner("Extracting syllabus..."):
            # Initialize progress bar
            p1 = st.progress(0)
            course = {}

            # Extract syllabi for each course
            for i, link in enumerate(st.session_state.course_links):
                p1.progress(int((i / len(st.session_state.course_links)) * 100))
                syllabus = extract_syllabus(link)
                course[f"course_{i+1}"] = syllabus

        p1.progress(100)  # Complete progress
        k = st.success("Syllabus Extracted")
        k.empty()
        p1.empty()
        # st.json(syllabi)

        if course:
            st.session_state.course_data = course
            with st.spinner("Generating syllabus..."):
                # Generate syllabus
                p2 = st.progress(35)
                syllabus = generate_response(course)
                p2.progress(100)
                p2.empty()
                st.text("Generated Syllabus:")
                st.markdown(syllabus)

                html_text = markdown.markdown(syllabus)
                pdf = convert_html_to_pdf(html_text)

                if pdf:
                    st.success("PDF generated successfully!")
                    st.download_button(
                        label="Download PDF",
                        data=pdf,
                        file_name="output.pdf",
                        mime="application/pdf",
                    )

            # Compute and display individual course contribution
            contributions = []
            total_sections = 0
            all_sections = []
            print("*****************************************")
            for course_key, course_data in course.items():
                print(course_key, course_data)
                print("************")
                course_title = course_data["course_title"]
                syllabus_sections = course_data["syllabus"]
                section_count = len(syllabus_sections)
                total_sections += section_count
                all_sections.extend(syllabus_sections.keys())
                contributions.append(
                    {"Course": course_title, "Sections": section_count}
                )

            contributions_df = pd.DataFrame(contributions)
            contributions_df["Percentage"] = (
                contributions_df["Sections"] / total_sections
            ) * 100

            st.subheader("Individual Course Contributions:")
            # st.dataframe(contributions_df)

            styled_table = contributions_df.to_html(classes="styled-table", index=False)

            table_style = """
            <style>
            .styled-table {
                border-collapse: collapse;
                margin: 25px 0;
                font-size: 18px;
                text-align: left;
                width: 100%;
            }
            .styled-table thead tr {
                background-color: #009879;
                color: #ffffff;
                text-align: left;
                font-weight: bold;
            }
            .styled-table th, .styled-table td {
                padding: 12px 15px;
                border: 1px solid #dddddd;
            }
            .styled-table tbody tr {
                background-color: #000000; /* Black background for all rows */
                color: #ffffff; /* White text for readability */
                border-bottom: 1px solid #dddddd;
            }
            </style>
            """
            st.markdown(table_style, unsafe_allow_html=True)

            st.markdown(styled_table, unsafe_allow_html=True)

            # List common topics across all courses
            v = str(course)
            print(v)
            common_sections = common_topics(v)

            print(common_sections)

            st.text("Common Topics Across All Courses:")
            st.write(common_sections)

        else:
            st.error("No syllabi extracted.")
    else:
        st.error("Please enter at least one Udemy course link.")
