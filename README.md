# metabase-google-auth

Module for Metabase with Google Authentication login.

# How to use
### Install dependencies
pip install -r requirements.txt

### Setup login info
Edit config.py with your login email and password.

Then get session token by

```python
MetabaseAuth.get_cookie(domain)
```
If 2-step authentication is enabled you need to grant access using your phone.
The session token can be stored and reuse until expiration.

### Query unfiltered question into DataFrame
Example: get the results for question ID 12345, convert into a DataFrame and export to csv
```python
import MetabaseAuth
import config

domain = 'metabase.xxxxx.xx'
token = MetabaseAuth.get_cookie(domain)

df = MetabaseAuth.query(domain, token, 12345, export=True)
```

### Query filtered question
For questions with filters, first we need to obtain the format of the question's parameters request. Get the params as a list by
```python
params = MetabaseAuth.get_params(domain, question_id)
```
This will open the login page again and navigate to the question page. To get the params, put some values into the filters and click run on Metabase.

Example: query a filtered question with ID 12345
```python
params = MetabaseAuth.get_params(domain, question_id)

df = MetabaseAuth.query(domain, token, 12345, params=params)
```

### Modify params
Once params has been obtained, we can either convert it to a string and modify directly, or treat it as a list of dictionary for more complex automation.

Example of a returned params:
```python
# creation_datetime is a Field Fiter with value '2020-12-01~2020-12-31'
# order_id is a normal filter with value '111'
[{'type': 'date/range',
  'target': ['dimension', ['template-tag', 'creation_datetime']],
  'value': '2020-12-01~2020-12-31'},
 {'type': 'category',
  'target': ['variable', ['template-tag', 'order_id']],
  'value': '111'}]
```
#### Convert params to string
We can convert the params to a parsable string, modify the values and pass it to another query call.
```python
params_str = MetabaseAuth.params_formatting(params)
```
