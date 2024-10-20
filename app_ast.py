import streamlit as st
import sqlite3
import json
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

# Define AST Node Classes
class ASTNode:
    pass

class BinaryOperation(ASTNode):
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right

class Literal(ASTNode):
    def __init__(self, value):
        self.value = value

class Field(ASTNode):
    def __init__(self, name):
        self.name = name

class LogicalOperation(ASTNode):
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right

# SQL to JSON conversion function
def sql_to_json(sql):
    sql = sql.strip()

    # Regex to capture basic conditions (including AND/OR)
    pattern = r"(\w+)\s*(=|!=|<|<=|>|>=)\s*([0-9]+|'[^']+')"
    conditions = re.findall(pattern, sql)

    if not conditions:
        return None

    # Initialize JSON structure
    json_conditions = []

    for condition in conditions:
        left, operator, right = condition
        if right.startswith("'") and right.endswith("'"):
            right = right[1:-1]  # Remove quotes

        json_conditions.append({
            "operator": operator,
            "left": left,
            "right": int(right) if right.isdigit() else right
        })

    # Check for AND/OR operations
    if 'AND' in sql:
        return {
            "type": "AND",
            "conditions": json_conditions
        }
    elif 'OR' in sql:
        return {
            "type": "OR",
            "conditions": json_conditions
        }

    # Single condition case
    return {
        "type": "SINGLE",
        "conditions": json_conditions
    }

# Parsing rules into AST
def parse_rule(rule_dict):
    if rule_dict['type'] == "SINGLE":
        conditions = rule_dict['conditions']
        return [BinaryOperation(Field(cond['left']), cond['operator'], Literal(cond['right'])) for cond in conditions]

    elif rule_dict['type'] in ["AND", "OR"]:
        left_conditions = []
        for condition in rule_dict['conditions']:
            left_conditions.append(BinaryOperation(Field(condition['left']), condition['operator'], Literal(condition['right'])))
        
        return LogicalOperation(left_conditions, rule_dict['type'], None)

# Evaluating the AST
def evaluate_ast(node, data):
    if isinstance(node, Literal):
        return node.value
    elif isinstance(node, Field):
        return data.get(node.name)
    elif isinstance(node, BinaryOperation):
        left_value = evaluate_ast(node.left, data)
        right_value = evaluate_ast(node.right, data)

        if node.operator == '=':
            return left_value == right_value
        elif node.operator == '!=':
            return left_value != right_value
        elif node.operator == '<':
            return left_value < right_value
        elif node.operator == '<=':
            return left_value <= right_value
        elif node.operator == '>':
            return left_value > right_value
        elif node.operator == '>=':
            return left_value >= right_value
            
    elif isinstance(node, LogicalOperation):
        results = []
        for cond in node.left:
            results.append(evaluate_ast(cond, data))
        if node.operator == "AND":
            return all(results)
        elif node.operator == "OR":
            return any(results)

    return False

# UI Design
st.set_page_config(page_title="RuleCrafter", layout="wide")

# Page Title with subscript
st.markdown("<h1 style='text-align: center; color: #4CAF50;'>RuleCrafter</h1>", unsafe_allow_html=True)
st.markdown("<h6 style='text-align: center; color: gray; font-size: 18px;'>Rule Engine Application</h6>", unsafe_allow_html=True)

# Add Rule Section
st.markdown("## Add a New Rule", unsafe_allow_html=True)
with st.expander("Click to Add a New Rule", expanded=True):
    with st.form(key="rule_form", clear_on_submit=True):
        rule_string = st.text_area("Enter a rule in SQL format (e.g., age = 30 AND department = 'Sales')", height=150)
        submit_rule = st.form_submit_button("Add Rule", use_container_width=True)

        if submit_rule:
            if rule_string:
                try:
                    # Convert SQL to JSON
                    rule_json = sql_to_json(rule_string)

                    # Store the original SQL string in the database
                    c.execute("INSERT INTO rules (rule_string) VALUES (?)", (rule_string,))
                    conn.commit()
                    st.success(f"✅ Rule added successfully!")
                except Exception as e:
                    st.error(f"🚫 Error while processing the rule: {str(e)}")
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
    results = []

    c.execute("SELECT * FROM rules")
    rules = c.fetchall()

    for rule in rules:
        try:
            # Convert SQL to JSON
            rule_json = sql_to_json(rule[1])
            if rule_json:
                rule_ast = parse_rule(rule_json)
                if isinstance(rule_ast, list):  # Handle multiple conditions
                    result = all(evaluate_ast(cond, user_data) for cond in rule_ast)
                else:
                    result = evaluate_ast(rule_ast, user_data)
                results.append((rule[1], result))
            else:
                results.append((rule[1], "⚠️ Error in parsing SQL statement."))
        except Exception as e:
            results.append((rule[1], f"⚠️ Error in rule: {str(e)}"))

    for rule_string, result in results:
        if isinstance(result, bool):
            if result:
                st.success(f"✅ User satisfies the rule: `{rule_string}`")
            else:
                st.warning(f"⚠️ User does not satisfy the rule: `{rule_string}`")
        else:
            st.error(result)

# Close SQLite connection
conn.close()
