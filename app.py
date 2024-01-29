import requests,os
import shutil
import json
from veryfi import Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_rec_id_from_api(file_to_read_path, file_to_search_id_path):
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    username = os.getenv("APP_USERNAME")
    api_key = os.getenv("API_KEY")

    categories = [
    "Administratiekosten",
    "Advieskosten",
    "Afrondingsverschillen",
    "Bankkosten",
    "Kantoorbenodigdheden",
    "Kleine aanschaffingen (< 450 euro)",
    "Opleidingskosten ondernemer",
    "Porti",
    "Software",
    "Telefoon en internet",
    "Vakliteratuur",
    "Verzekeringen algemeen",
    "Huisvestingskosten",
    "Kosten auto van de zaak",
    "Brandstof auto van de zaak",
    "Brandstofkosten",
    "Btw op privé-gebruik auto van de zaak",
    "Onderhoud en reparatie auto",
    "Overige kosten auto van de zaak",
    "Privé-gebruik auto van de zaak",
    "Ongecategoriseerde uitgaven",
    "Verkoopkosten",
    "Bedrijfskleding",
    "Donations",
    "Eten en drinken met relaties",
    "Reclame- en advertentiekosten",
    "Relatiegeschenken",
    "Verteerkosten",
    "Vervoerskosten",
    "Kilometervergoeding",
    "Parkeerkosten",
    "Reis- en verblijfkosten"
]

    file_path = file_to_read_path

    # Initialize the Veryfi client
    veryfi_client = Client(client_id, client_secret, username, api_key)

    # Submit the document for processing
    response = veryfi_client.process_document(file_path, categories=categories)

    # Check if the request was successful (status code 200)
    if type(response) is dict:
        # Parse the response text as JSON
        res_dict = response
        json_file = open(file_to_search_id_path, 'r')
        data_dict = json.load(json_file)
        
        # Extract the target criteria from the API response
        target_contra_account_name = res_dict.get("vendor").get("name").lower()
        target_date = res_dict.get("date").split(" ")[0].split("-")
        year_month = target_date[0]+target_date[1]
        price = res_dict.get("total")
        if 'collect' in target_contra_account_name:
            target_contra_account_name = 'Greenwheels'
        print(target_contra_account_name,target_date,price)
        # Iterate through the list and find the matching object
        matching_id = None
        for item in data_dict:
            if (item["contra_account_name"] is None) or (item["amount"] is None) or (item["date"] is None):
                pass
            else:
                if item["contra_account_name"].lower() in target_contra_account_name.lower() and abs(float(item["amount"])) == price:
                    matching_id = item["id"]
                    return True,matching_id,res_dict
    else:
        print(f"Got Error for {file_to_read_path}.")
        return False,None,None

def get_tax_id(target_percentage):

    # Read the JSON file
    with open('tax_rates.json', 'r') as file:
        tax_rates_data = json.load(file)

    # Iterate through the objects and find the one with the target percentage
    matching_id = "351095402453271688"
    for tax_rate_info in tax_rates_data:
        if tax_rate_info["percentage"]:
            if target_percentage in tax_rate_info["percentage"]:
                matching_id = tax_rate_info["id"]
                break

    return matching_id

def get_contact_id(query, default_id):
    url = f"https://moneybird.com/api/v2/341859963860158294/contacts/?query={query}"
    headers = {
        "Authorization": "Bearer pCSVAoCxGSbQvIT4jX6aTLG82FisDcdcB9-GS2AAbvA",
        "Content-Type": "application/json",
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        # Successfully retrieved the data
        data = response.json()
        for contact in data:
            company_name = contact.get("company_name", "").lower()
            if query in company_name:
                return contact["id"]
        
        # If no match found, return the default ID
        return default_id

    else:
        # Handle error
        print(f"Error: {response.status_code} - {response.text}")
        # Return the default ID in case of an error
        return default_id

def patch_financial_mutations_with_data(acc_id, rec_id, access_token, data):
    url = f"https://moneybird.com/api/v2/{acc_id}/financial_mutations/{rec_id}/link_booking.json"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.patch(url, headers=headers, json=data)
        response.raise_for_status()  # Check for any HTTP errors

        if response.status_code == 200:
            print("Purchase Invoice Added. PATCH request successful")
            return True
        else:
            print(f"PATCH request for Purchase Invoice failed with status code {response.status_code} Text => {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return False

def get_invoice_id_from_financial_mutation(acc_id, rec_id, access_token):
    url = f"https://moneybird.com/api/v2/{acc_id}/financial_mutations/{rec_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Check for any HTTP errors

        data = response.json()
        payments = data.get("payments", [])
        # Loop through payments to find the invoice_id
        for payment in payments:
            invoice_id = payment.get("invoice_id")
            if invoice_id:
                print(f"Got Invoice id => {invoice_id}")
                return invoice_id

        # If no invoice_id found in payments, return None
        return False

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return False

def patch_purchase_invoices(acc_id, invoice_id, access_token, data):
    url = f"https://moneybird.com/api/v2/{acc_id}/documents/purchase_invoices/{invoice_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.patch(url, headers=headers, json=data)
        response.raise_for_status()  # Check for any HTTP errors

        if response.status_code == 200:
            print("All Data Successfully Added.Patch request successful")
            return True
        else:
            print(f"PATCH request failed with status code {response.status_code}")
            print(response.text)
            return False

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return False

def upload_attachement(acc_id, invoice_id, access_token, file_path):
    url = f"https://moneybird.com/api/v2/{acc_id}/documents/purchase_invoices/{invoice_id}/attachments.json"
    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    files = {
    'file': (f'{file_path}', open(f'{file_path}', 'rb'), 'application/pdf'),
    # Add more files as needed
}

    data = {
        "filename": f"{file_path}",
        "content_type": "application/pdf",
    }

    response = requests.post(url, headers=headers, files=files, data=data)


    if response.status_code == 200:
        print("Attachment uploaded")
        return True
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return False

def get_financial_mutation_data(acc_id, rec_id, access_token):
    url_to_get_base_price = f"https://moneybird.com/api/v2/{acc_id}/financial_mutations/{rec_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    response = requests.get(url_to_get_base_price, headers=headers)
    response.raise_for_status()  # Check for any HTTP errors

    res_data = response.json()
    return res_data

def parse_pdf_from_api(file_path):
    status = False
    client_id = 'vrfBjzjWAoOF2OsfCjP9GRCXXLB31NrwF12C3ei'
    client_secret = 'GeYW0Mx9CTp8hdIyLbZsnNcCwE4luGKrpNOGGo0UznYctzmkoLkzDdmnKSZl5iLC7VuiCo0T3taRJroHYI22LhuTudLp3bZshN4ylHbAIpBc0gE3UsXCKv4ClExZucL4'
    username = 'muhammadab3321'
    api_key = 'd855eaa31f565fab87b7e4f34b36fa88'

    categories = ['Grocery', 'Utilities', 'Travel','Legal & Professional Services']
    try:
        # This submits document for processing (takes 3-5 seconds to get response)
        veryfi_client = Client(client_id, client_secret, username, api_key)
        response = veryfi_client.process_document(file_path, categories=categories)
        return True,response
    except Exception as e:
        return status,str(e)

def delete_record_by_id(json_obj, id_to_delete):
    # Check if the JSON object is a string, and parse it into a dictionary if needed
    if isinstance(json_obj, str):
        json_obj = json.loads(json_obj)
    
    # Check if the JSON object is a list
    if isinstance(json_obj, list):
        # Iterate through the list to find the record with the specified ID
        for item in json_obj:
            if 'id' in item and item['id'] == id_to_delete:
                json_obj.remove(item)
                print(f"{id_to_delete} Removed.")
                return json_obj
    else:
        # If the JSON object is a dictionary, check if it contains the specified ID
        if 'id' in json_obj and json_obj['id'] == id_to_delete:
            return None  # Return None to indicate that the record was deleted
    
    # If the ID was not found, return the original JSON object
    return json_obj

def delete_id_from_json_file(rec_id,file_path):
    try:
        with open(file_path, 'r') as file:
            json_data = json.load(file)
    except FileNotFoundError:
        print(f"The file '{file_path}' does not exist.")
        exit()
    result = delete_record_by_id(json_data,rec_id)
    if result is None:
        print(f"Record with ID {rec_id} not found.")
    else:
        with open(file_path, 'w') as file:
            json.dump(result, file, indent=4)

        print(f"Record with ID {rec_id} deleted successfully.")

def run_job(acc_id,access_token,file_path,financial_data_file='financial_data.json'):
    # Get data of financial mutation
    print(f"For {file_path} intiating api call to get data")
    result = get_rec_id_from_api(file_path, financial_data_file)
    id = None
    if result is not None:
        parse_api_status, id, parsed_data = result
        with open("new.json",'w') as file:
            file.write(json.dumps(parsed_data))
        # Continue with your code using parse_api_status, id, and parsed_data
    else:
        # Handle the case when the function returns None
        print("Error: get_rec_id_from_api returned None")
    print(f"For {file_path} id is {id}")
    if parse_api_status:
        rec_id = id
        print(f"For {file_path} api call Success For data. Now Starting get_financial_mutation_data")
        data_of_financial_mutations = get_financial_mutation_data(acc_id, rec_id, access_token)
        price_base = abs(float(data_of_financial_mutations.get("amount")))
        data_to_patch_financial_mutations = {
            "booking_type": "NewPurchaseInvoice",
            "price_base": price_base
        }
        print(f"for Rec_id {rec_id} Successfully got financial_mutation_data")

        res_patch_purchase_invoice = patch_financial_mutations_with_data(acc_id, rec_id, access_token, data_to_patch_financial_mutations)
        if res_patch_purchase_invoice:
            print(f"For Rec id {rec_id} Successfully patched financial_mutation_data")
            invoice_id = get_invoice_id_from_financial_mutation(acc_id, rec_id, access_token)
            
            if invoice_id:
                # Get json data from api by parsing the PDF
                print(f"For Rec id {rec_id} intiating api call to get data")
                line_items = {}
                items = parsed_data["line_items"]
                # Define the data to append for each item with index as key
                for idx, item in enumerate(items):
                    if item["price"]:
                        price_base = item["price"]
                    else:
                        price_base = 0.00
                    if item["tax_rate"]:
                        tax_rate_id = get_tax_id(str(item["tax_rate"]))
                        print(f"For Rec id {rec_id} Got Tax ID : {tax_rate_id}")
                    elif (item["tax_rate"] is None) and (('21' in str(item["tax"]) or ('9' in str(item["tax"])) or ('6' in str(item["tax"])))):
                        tax_rate_id = get_tax_id(str(item["tax"]))
                        print(f"For Rec id {rec_id} Got Tax ID : {tax_rate_id}")
                    else:
                        tax_rate_id = get_tax_id(str('123'))
                        print(f"For Rec id {rec_id} Got Tax ID : {tax_rate_id}")


                    # Append data for the current item with index as key
                    line_items[str(idx)] = {
                            "amount": str(item["quantity"]),
                            "description": rf'{item["text"]}',
                            "period": "",
                            "price": str(price_base).replace('.', ','),
                            "tax_rate_id": str(tax_rate_id),
                            "ledger_account_id": "378740509306259358",
                            "_destroy": False,
                            "row_order": 0,
                            "product_id": "",
                            "automated_tax_enabled": False
                        }
                
                query = parsed_data.get("vendor").get("name").split(" ")[0].lower()
                contact_id = get_contact_id(query, "389414139562296700")
                print(f"For {file_path} Got Contact ID : {contact_id}")
                # Resulting list of appended data with index as key
                data_to_patch_to_purchase_invoices = {
                                                    "purchase_invoice": {
                                                        "contact_id": str(contact_id),
                                                        "reference": f'{data_of_financial_mutations.get("contra_account_name")}',
                                                        "date": f'{parsed_data.get("date").split(" ")[0]}',
                                                        "due_date": None,
                                                        "currency": f'{data_of_financial_mutations.get("currency")}',
                                                        "revenue_invoice": False,
                                                        "prices_are_incl_tax": True,
                                                        "details_attributes": line_items
                                                    }
                                                }
                
                res_patch_purchase_invoice = patch_purchase_invoices(acc_id,invoice_id,access_token,data_to_patch_to_purchase_invoices)
                if res_patch_purchase_invoice:
                    print(f"For {file_path} patch_purchase_invoices Success")
                    document_id = invoice_id
                    res_upload_attachement = upload_attachement(acc_id, document_id, access_token, file_path)
                    if res_upload_attachement:
                        print(f"For  For Rec id : {rec_id} Got Success.")
                        delete_id_from_json_file(rec_id,financial_data_file)
                    else:
                        print("Attachement Uploaded Failed.")
                else:
                    print("Could Not start patch_purchase_invoices")
            else:
                print("Could Not start patch_purchase_invoices due to missing invoice_id")
        else:
            print("Could Not start getting invoice id")
    else:
        print(f"Could Not Find Id For {file_path}")

# Define the folder containing the files
folder_path = "data_to_proccess"  # Replace with the actual folder path
proccessed_folder_path = "proccessed_data"
# List all files in the folder
file_list = os.listdir(folder_path)

# Specify the file extensions to process
valid_extensions = (".pdf", ".png", ".jpg", ".jpeg", ".gif")  # Add more extensions if needed

# Iterate over each file and run the job
for file_name in file_list:
    if file_name.lower().endswith(valid_extensions):
        file_path = os.path.join(folder_path, file_name)
        acc_id = os.getenv("ACC_ID")
        access_token = os.getenv("ACCESS_TOKEN")
        print(f"Processing file: {file_name}")
        try:
            run_job(acc_id,access_token,file_path)
            destination_path = os.path.join(proccessed_folder_path, file_name)
            shutil.move(file_path, destination_path)
            print(f"File '{file_name}' moved to '{proccessed_folder_path}'")
        except Exception as e:
            print(f"Error processing file '{file_name}' Got Error {str(e)}")
            continue
    else:
        print(f"File {file_name} is not valid")
