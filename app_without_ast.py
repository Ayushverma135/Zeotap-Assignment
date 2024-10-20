import streamlit as st
import sqlite3
import re

# SQLite connection setup
conn = sqlite3.connect('rules.db', check_same_thread=False)
c = conn.cursor()

# Create the rules table if not exists
c.execute('''
CREATE TABLE IF NOT EXISTS rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_string TEXT NOT NULL
)
''')
conn.commit()

# Rule class to represent a single rule
class Rule:
    def __init__(self, field, operator, value):
        self.field = field.strip()
        self.operator = operator.strip()
        self.value = value.strip()

    def evaluate(self, data):
        if self.field in data:
            field_value = data[self.field]

            # Adjust value conversion based on the data type
            if isinstance(field_value, int):
                value = int(self.value) if self.value.isdigit() else self.value
            else:
                value = str(self.value).strip('\"\'')  # Clean quotes for string comparison

            # Use eval to evaluate the condition
            valid_operators = {
                '==': lambda x, y: x == y,
                '!=': lambda x, y: x != y,
                '<': lambda x, y: x < y,
                '<=': lambda x, y: x <= y,
                '>': lambda x, y: x > y,
                '>=': lambda x, y: x >= y
            }

            if self.operator in valid_operators:
                return valid_operators[self.operator](field_value, value)

        return False

# Composite rule to handle multiple conditions
class CompositeRule:
    def __init__(self, operator):
        self.operator = operator
        self.rules = []

    def add_rule(self, rule):
        self.rules.append(rule)

    def evaluate(self, data):
        results = [rule.evaluate(data) for rule in self.rules]
        if self.operator == 'AND':
            return all(results)
        elif self.operator == 'OR':
            return any(results)
        return False

# Function to create a rule object from string
def parse_rule(rule_string):
    rule_string = rule_string.replace('=', '==')
    rule_string = re.sub(r'\s*==\s*', ' == ', rule_string)
    rule_string = re.sub(r'\s*!=\s*', ' != ', rule_string)
    rule_string = re.sub(r'\s*<\s*', ' < ', rule_string)
    rule_string = re.sub(r'\s*>\s*', ' > ', rule_string)
    rule_string = re.sub(r'\s*<=\s*', ' <= ', rule_string)
    rule_string = re.sub(r'\s*>=\s*', ' >= ', rule_string)
    
    tokens = re.split(r'\s+(AND|OR)\s+', rule_string.strip())
    if len(tokens) == 1:
        parts = tokens[0].strip().split()
        return Rule(parts[0], parts[1], ' '.join(parts[2:]))
    
    composite_rule = CompositeRule(tokens[1])
    parts1 = tokens[0].strip().split()
    parts2 = tokens[2].strip().split()
    
    composite_rule.add_rule(Rule(parts1[0], parts1[1], ' '.join(parts1[2:])))
    composite_rule.add_rule(Rule(parts2[0], parts2[1], ' '.join(parts2[2:])))
    
    return composite_rule

# UI Design
st.set_page_config(page_title="RuleCrafter", layout="wide")

# Page Title with subscript
st.markdown("<h1 style='text-align: center; color: #4CAF50;'>RuleCrafter</h1>", unsafe_allow_html=True)
st.markdown("<h6 style='text-align: center; color: gray; font-size: 18px;'>Rule Engine Application</h6>", unsafe_allow_html=True)

# Add Rule Section
st.markdown("## Add a New Rule", unsafe_allow_html=True)
with st.expander("Click to Add a New Rule", expanded=True):
    with st.form(key="rule_form", clear_on_submit=True):
        rule_string = st.text_input("Enter a rule (e.g., age > 30 AND department == 'Sales')", max_chars=100)
        submit_rule = st.form_submit_button("Add Rule", use_container_width=True)

        if submit_rule:
            if rule_string:
                c.execute("INSERT INTO rules (rule_string) VALUES (?)", (rule_string,))
                conn.commit()
                st.success(f"✅ Rule '{rule_string}' added successfully!")
            else:
                st.error("🚫 Rule string cannot be empty!")

# Display Existing Rules
st.markdown("## Existing Rules", unsafe_allow_html=True)
c.execute("SELECT * FROM rules")
rules = c.fetchall()

if rules:
    for idx, rule in enumerate(rules, start=1):
        st.markdown(f"**Rule {idx}:** `{rule[1]}`")
else:
    st.info("ℹ️ No rules available yet.")

# Remove Rule Section
st.markdown("## Remove a Rule", unsafe_allow_html=True)
if rules:
    with st.expander("Click to Remove a Rule", expanded=False):
        remove_rule_idx = st.selectbox("Select Rule Number to Remove", options=[f"Rule {idx}" for idx in range(1, len(rules) + 1)])
        remove_button = st.button("Remove Rule")

        if remove_button and remove_rule_idx:
            rule_num = int(remove_rule_idx.split()[1]) - 1
            rule_id = rules[rule_num][0]

            # Remove rule from the database
            c.execute("DELETE FROM rules WHERE id = ?", (rule_id,))
            conn.commit()
            st.success(f"✅ Rule '{rules[rule_num][1]}' removed successfully!")
else:
    st.info("ℹ️ No rules to remove.")

# Evaluation Section
st.markdown("## Evaluate Rules", unsafe_allow_html=True)

st.markdown("### Provide Input Data:")
col1, col2 = st.columns(2)
with col1:
    user_data = {}
    user_data['age'] = st.number_input("Age", min_value=0, max_value=100)
    user_data['experience'] = st.number_input("Experience (in years)", min_value=0)

with col2:
    user_data['department'] = st.selectbox("Department", options=["Sales", "Marketing", "Engineering", "HR"])
    user_data['salary'] = st.number_input("Salary", min_value=0)

# Evaluate button
evaluate_button = st.button("Evaluate Rules", use_container_width=True)

if evaluate_button:
    composite_rule = CompositeRule("AND")
    c.execute("SELECT * FROM rules")
    rules = c.fetchall()

    for rule in rules:
        rule_object = parse_rule(rule[1])
        composite_rule.add_rule(rule_object)

    result = composite_rule.evaluate(user_data)

    if result:
        st.success("✅ User satisfies all the rules!")
    else:
        st.warning("⚠️ User does not satisfy the rules.")

# Close SQLite connection
conn.close()