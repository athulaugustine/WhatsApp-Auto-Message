import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pyautogui
import os

img_flag = False

def open_image_in_viewer(image_path):
    os.startfile(image_path)

def save_image_to_current_directory(image_file):
    if image_file:
        try:
            image_path = os.path.join(os.getcwd(), image_file.name)  # Construct full path to save the image
            with open(image_path, "wb") as f:
                f.write(image_file.read())  # Use image_file.read() to get the bytes and write them
            print(f"Image saved successfully to {image_path}")
        except Exception as e:
            print(f"Error saving image: {e}")
        return image_path
# Function to send a WhatsApp message using Selenium
def copy_image_to_clipboard(image_path):
    open_image_in_viewer(image_path)
    time.sleep(2)  # Wait for the image to be opened
    pyautogui.hotkey('ctrl', 'c')  # Copy the selected image to the clipboard
    time.sleep(2)

def send_whatsapp_message(driver, contact_number, message, image_flag):
    new_chat_btn = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, '//div[@title="New chat"]'))
    )
    new_chat_btn.click() #Search name or number
    time.sleep(2)
    search_box = driver.find_element("xpath", '/html/body/div[1]/div/div/div[2]/div[2]/div[1]/span/div/span/div/div[1]/div[2]/div[2]/div/div[1]/p')
    search_box.click()
    time.sleep(2)
    search_box.send_keys(contact_number)
    time.sleep(2)
    search_box.send_keys(Keys.ENTER)
    time.sleep(2)  # Wait for the chat to open

    if image_flag:
        message_box = driver.find_element("xpath", '/html/body/div[1]/div/div/div[2]/div[4]/div/footer/div[1]/div/span[2]/div/div[2]/div[1]/div/div[1]/p')
        time.sleep(2)
        message_box.click()
        time.sleep(2)
        pyautogui.hotkey('ctrl', 'v')  # Paste the image into the chat
        time.sleep(2)
        message_box = driver.find_element("xpath", '/html/body/div[1]/div/div/div[2]/div[2]/div[2]/span/div/div/div/div[2]/div/div[1]/div[3]/div/div/div[2]/div[1]/div[1]/p')
        message_box.click()
        time.sleep(2)
        message_box.send_keys(message)
        time.sleep(2)
        message_box.send_keys(Keys.ENTER)
        time.sleep(2)
        
    elif message:
        message_box = driver.find_element("xpath", '/html/body/div[1]/div/div/div[2]/div[4]/div/footer/div[1]/div/span[2]/div/div[2]/div[1]/div/div[1]/p')
        message_box.click()
        message_box.send_keys(message)
        message_box.send_keys(Keys.ENTER)
        time.sleep(2)  # Wait for the message to be sent

# File uploader for Excel file
customer_excel = st.file_uploader("Upload customer Excel file", type=["xlsx"])

if customer_excel:
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
        "Hi {customer_name}, Whats up ?",
    )
    st.write(txt.format(customer_name=selected_dataframe['Customer Name'][0]))
    
    # File uploader for image file
    image_file = st.file_uploader("Upload image to send", type=["jpg", "jpeg", "png"])

    if image_file:
        image_path = save_image_to_current_directory(image_file)
        st.image(image_file, caption="Uploaded Image", use_column_width=True)
    else:
        image_path = None

    # Send message button
    if st.button("Send Message!"):
        if image_file:
            img_flag = True
            copy_image_to_clipboard(image_path)
        driver = webdriver.Chrome()
        driver.get("https://web.whatsapp.com")
        st.write("Please scan the QR code to log in to WhatsApp Web.")
        time.sleep(25)
        for _, row in selected_dataframe.iterrows():
            if row['Select']:
                contact_number = row['Contact No.']
                send_whatsapp_message(driver, contact_number, txt.format(customer_name=row['Customer Name']),img_flag)
        driver.quit()
        st.success("Messages sent successfully!")

# Running the Streamlit app:
# Use the command: streamlit run your_script_name.py
