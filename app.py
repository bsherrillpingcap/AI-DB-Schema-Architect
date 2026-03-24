import os
import json
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="AI DB Schema Architect", page_icon="🧠", layout="wide")


def get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set.")
    return OpenAI(api_key=api_key)


SYSTEM_PROMPT = """
You are a senior data architect.

Given an application description, generate a relational database design.

Return valid JSON with this shape:
{
  "app_name": "string",
  "summary": "string",
  "tables": [
    {
      "name": "string",
      "purpose": "string",
      "columns": [
        {
          "name": "string",
          "type": "string",
          "nullable": true,
          "description": "string"
        }
      ],
      "primary_key": ["string"],
      "foreign_keys": [
        {
          "column": "string",
          "references_table": "string",
          "references_column": "string"
        }
      ],
      "indexes": ["string"]
    }
  ],
  "relationships": [
    {
      "from_table": "string",
      "to_table": "string",
      "type": "one-to-many | many-to-one | many-to-many | one-to-one",
      "notes": "string"
    }
  ],
  "sql": "string"
}

Rules:
- Prefer normalized relational design.
- Use practical naming conventions.
- Include created_at and updated_at where appropriate.
- Generate TiDB-compatible SQL.
- Return JSON only. No markdown fences.
""".strip()


def generate_schema(app_description: str) -> dict:
    client = get_client()

    response = client.responses.create(
        model="gpt-4.1",
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Application description:\n{app_description}"
            }
        ]
    )

    text = response.output_text.strip()
    return json.loads(text)


st.title("🧠 AI DB Schema Architect")
st.caption("Design your database just by describing your app.")

with st.sidebar:
    st.header("Setup")
    st.write("1. Set your OPENAI_API_KEY environment variable.")
    st.write("2. Describe your app.")
    st.write("3. Generate a starter schema.")

example_prompt = (
    "Build a gaming platform with players, teams, tournaments, matches, rewards, "
    "and leaderboard history."
)

app_description = st.text_area(
    "Describe your app",
    value=example_prompt,
    height=180,
    placeholder="Describe your application, users, key entities, and workflows..."
)

if st.button("Generate Schema", type="primary"):
    if not app_description.strip():
        st.warning("Please enter an application description.")
    else:
        try:
            with st.spinner("Generating schema..."):
                result = generate_schema(app_description)

            st.subheader("Summary")
            st.write(result.get("summary", ""))

            st.subheader("Tables")
            for table in result.get("tables", []):
                with st.expander(table["name"], expanded=False):
                    st.write(f"**Purpose:** {table.get('purpose', '')}")
                    st.write("**Columns**")
                    st.dataframe(table.get("columns", []), use_container_width=True)
                    st.write(f"**Primary Key:** {', '.join(table.get('primary_key', [])) or 'N/A'}")
                    st.write("**Foreign Keys:**")
                    st.json(table.get("foreign_keys", []))
                    st.write(f"**Indexes:** {', '.join(table.get('indexes', [])) or 'N/A'}")

            st.subheader("Relationships")
            st.json(result.get("relationships", []))

            st.subheader("Generated SQL")
            st.code(result.get("sql", ""), language="sql")

            st.subheader("Raw JSON")
            st.json(result)

        except json.JSONDecodeError:
            st.error("The model did not return valid JSON. Try again or tighten the prompt.")
        except Exception as exc:
            st.error(f"Error: {exc}")
