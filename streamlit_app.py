import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from datetime import datetime
import tempfile

def save_google_contacts_csv(error_list):
    print(error_list)
    if not error_list:
        st.info("No failed contacts to save.")
        return
    
    # Define Google Contacts CSV columns
    google_contacts_columns = [
        "First Name", "Middle Name", "Last Name", "Phonetic First Name", "Phonetic Middle Name", "Phonetic Last Name",
        "Name Prefix", "Name Suffix", "Nickname", "File As", "Organization Name", "Organization Title", "Organization Department",
        "Birthday", "Notes", "Photo", "Labels", "Phone 1 - Label", "Phone 1 - Value"
    ]
    
    contacts_data = []
    for contact_number, customer_name  in error_list.items():
        name_parts = customer_name.split()
        first_name = name_parts[0] if len(name_parts) > 0 else ""
        middle_name = name_parts[1] if len(name_parts) > 2 else ""
        last_name = name_parts[2] if len(name_parts) > 2 else name_parts[1] if len(name_parts) == 2 else ""
        
        contacts_data.append([
            first_name, middle_name, last_name, "", "", "", "", "", "", "", "", "", "", "", "", "", "* myContacts",
            "Mobile", contact_number
        ])
    
    df = pd.DataFrame(contacts_data, columns=google_contacts_columns)
    
    # Create directory if not exists
    folder_path = "saved_contacts"
    os.makedirs(folder_path, exist_ok=True)
    
    # Save as CSV
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    file_name = f"failed_contacts_{timestamp}.csv"
    file_path = os.path.join(folder_path, file_name)
    df.to_csv(file_path, index=False, encoding="utf-8-sig")
    
    # Provide download link in Streamlit
    st.success(f"Failed contacts saved as Google Contacts CSV in {folder_path}!")
    st.download_button(
        label="Download Failed Contacts CSV",
        data=df.to_csv(index=False, encoding="utf-8-sig"),
        file_name=file_name,
        mime="text/csv"
    )


def open_image_in_viewer(image_path):
    os.startfile(image_path)

def save_file_to_temp_directory(file, temp_dir):
    try:
        file_path = os.path.join(temp_dir, file.name)
        with open(file_path, "wb") as f:
            f.write(file.read())
        st.success(f"File {file.name} saved successfully to {file_path}")
        return file_path
    except Exception as e:
        st.error(f"Error saving file {file.name}: {e}")
        return None

def is_logged_in(driver):
    try:
        # Check for an element that is only present after login
        search_box = driver.find_element(By.XPATH, '//button[@aria-label="Search or start new chat"]/div[2]')
        return search_box is not None
    except:
        return False    

def send_whatsapp_message(driver, contact_number, message, media_paths):
    try:
        # Wait for the 'New chat' button to be clickable
        new_chat_btn = WebDriverWait(driver, 30).until( 
            EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Search or start new chat"]/div[2]'))
        )
        new_chat_btn.click()  # Click on 'New chat'
        time.sleep(3)

        # Wait for the search box to be visible and interactable
        search_box = WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.XPATH, '//div[@contenteditable="true" and @data-tab="3"]'))
        )
        search_box.send_keys(contact_number)  # Input the contact number
        time.sleep(2)
        search_box.send_keys(Keys.ENTER)  # Select the contact
        time.sleep(3)  # Wait for the chat to open

        if media_paths:
            for media_path in media_paths:
                attachment_btn = WebDriverWait(driver, 30).until(
                    EC.element_to_be_clickable((By.XPATH, '//button[@title="Attach"]'))
                )
                attachment_btn.click()
                time.sleep(3)

                media_type = "image" if media_path.lower().endswith(("jpg", "jpeg", "png")) else "video"

                file_input = driver.find_element(By.XPATH, '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]')
                file_input.send_keys(media_path)
                time.sleep(10 if media_type == "video" else 3)  # Wait for the file to be uploaded
                
                send_btn = WebDriverWait(driver, 30).until(
                    EC.element_to_be_clickable((By.XPATH, '//div[@aria-label="Send"]'))
                )
                send_btn.click()
                time.sleep(5)

        if message:
            message_box = driver.find_element(By.XPATH, '//div[@aria-placeholder="Type a message"]')
            message_box.send_keys(message)
            message_box.send_keys(Keys.ENTER)
            time.sleep(3)  # Wait for the message to be sent
        print(f"Successfully sent to {contact_number}")    
        return True
    except Exception as e:
        print(f"Failed to send to {contact_number}")
        return False

# File uploader for Excel file
customer_excel = st.file_uploader(
    "Upload customer Excel file, must have the identical columns ['Customer ID', 'Customer Name', 'Contact No.']", 
    type=["xlsx"]
)

if customer_excel:
    error_list = {}
    # Read the Excel file
    data_df = pd.read_excel(customer_excel)
    # Filter relevant columns
    filtered_dataframe = pd.DataFrame(data_df, columns=['Customer ID', 'Customer Name', 'Contact No.'])
    # Add a 'Select' column for user selection
    filtered_dataframe['Select'] = True
    # Display the dataframe with a checkbox column for selection
    selected_dataframe = st.data_editor(
        filtered_dataframe,
        column_config={
            "Select": st.column_config.CheckboxColumn(
                "Select Customer?",
                help="Select the customers to add",
                default=True,
            )
        },
        hide_index=True,
    )
    
    # Text area for message input
    txt = st.text_area(
        "Message to send",
        placeholder ="Use '{customer_name}' for customer names.",
    )
    try:
        st.write(txt.format(customer_name=selected_dataframe['Customer Name'][0]))
    except IndexError:
        st.write("Replace '{' single curly braces with '{{' or fix formatting errors.")

    # Create a temporary directory with a datetime stamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    temp_dir = tempfile.mkdtemp(prefix=f"media_{timestamp}_")
    
    # File uploader for image file
    media_files = st.file_uploader("Upload media to send", type=["jpg", "jpeg", "png", "mp4"], accept_multiple_files=True)
    media_paths = []
    if media_files:
        for media_file in media_files:
            file_path = save_file_to_temp_directory(media_file, temp_dir)
            if file_path:
                media_paths.append(file_path)
            else:
                st.info("No media files uploaded.")

    # Send message button
    if st.button("Send Message!"):
        driver = webdriver.Chrome()
        st.write("Please scan the QR code to log in to WhatsApp Web.")
        while True:
            driver.get("https://web.whatsapp.com")
            time.sleep(15)
            if is_logged_in(driver):
                st.write("Logged in successfully!")
                break

        for _, row in selected_dataframe.iterrows():
            if row['Select']:
                contact_number = row['Contact No.']
                try:
                    driver.refresh()
                    time.sleep(5)
                    status = send_whatsapp_message(driver, contact_number, txt.format(customer_name=row['Customer Name']), media_paths)
                    if status:
                        pass
                    else:
                        error_list[contact_number] = row['Customer Name']
                except Exception as e:
                    st.write(f"Failed to send message to {contact_number} ({row['Customer Name']})")
        driver.quit()
        st.success("Done!")
        save_google_contacts_csv(error_list)
# Running the Streamlit app:
# Use the command: streamlit run your_script_name.py
