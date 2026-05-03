--- 
Description: Seed realistic dummy expenses for a specific user
arguement-hints : "<user-id> <count> <months>" 
allowed-tools: Read,Bash(python3:*)
---

Read database db.py to understand the expense table,scchemes and conncetion patterns.

User Input :- $Arguments

### 1. Parse Argument :-
Extract from $Arguments :- 
   user-id : int
   count : int
   months : int

If any argument is missing or not in correct format , provide hint to the user , that how he need to input :- 
Usage: /seed-expenses <user-id> <count> <months> :- 
Example :- /seed-expenses 1,2,6

## 2. Verify user exist :-
Befire generating anything , confirm the user_id exists  in the user table , if not stop and say no user id found with given id <user-id>

## 3.Generate and insert expenses
Write and run a Python script that:

Spreads expenses randomly across the past months
Uses these categories with realistic Indian descriptions and amounts (₹):
Food: 50–800
Transport: 20–500
Bills: 200–3000
Health: 100–2000
Entertainment: 100–1500
Shopping: 200–5000
Other: 50–1000
Distributes categories roughly proportionally (Food most common, Health and Entertainment least)
Uses the db connection pattern from db.py — do not hardcode the database filename
Uses parameterised queries only — no string formatting in SQL
Inserts all expenses in a single transaction — roll back everything if any insert fails

## 4. Confirm
print:-
- How many expenses were inserted
- the date range they span
- a sample of 2 inserted recoreds




