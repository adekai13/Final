import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

google_service_account_info = st.secrets['google_service_account']
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_dict(google_service_account_info, scopes=scope)

# Function to read data from Google Sheets
@st.cache_data(ttl=30)
def read_google_sheet(_credentials):
    try:
        client = gspread.authorize(_credentials)
        sheet = client.open('adil')
        worksheet = sheet.get_worksheet(0)  
        data = worksheet.get_all_values()

        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            return df
        else:
            st.write("No data available in the Google Sheet.")
            return None
    except Exception as e:
        st.write(f"An error occurred: {str(e)}")
        return None

# Function to calculate profit and return the DataFrame
def calculate_profit(selected_country, selected_salesperson, df):
    if df is not None:
        try:
            # Filter data based on selected country and/or salesperson
            if selected_country and selected_salesperson:
                filtered_data = df[(df["ShipCountry"] == selected_country) & (df["SalesPerson"] == selected_salesperson)]
            elif selected_country:
                filtered_data = df[df["ShipCountry"] == selected_country]
            elif selected_salesperson:
                filtered_data = df[df["SalesPerson"] == selected_salesperson]
            else:
                filtered_data = df

            # Convert columns to numeric data types
            filtered_data['Units_Sold'] = pd.to_numeric(filtered_data['Units_Sold'])
            filtered_data['Unit_Sales_Price'] = pd.to_numeric(filtered_data['Unit_Sales_Price'])
            filtered_data['Unit_Cost'] = pd.to_numeric(filtered_data['Unit_Cost'])

            # Calculate profit
            filtered_data["Profit"] = filtered_data["Units_Sold"] * (filtered_data["Unit_Sales_Price"] - filtered_data["Unit_Cost"])

            return filtered_data
        except Exception as e:
            st.write(f"An error occurred during profit calculation: {str(e)}")
            return None
    else:
        return None

# Function to plot dynamic graphs
def plot_dynamic_graph(df, x_variable, selected_country):
    st.subheader(f"Dynamic Graph for {x_variable} in {selected_country}")
    fig, ax = plt.subplots()  # Create a Matplotlib figure
    sns.histplot(data=df, x=x_variable, kde=True, ax=ax)
    st.pyplot(fig)  # Pass the figure explicitly to st.pyplot()

# Streamlit app
st.title("Dynamic Graphs and Profit Calculation")

# Read data from Google Sheets
df = read_google_sheet(credentials)

# Store the last fetched data
last_data = df.copy() if df is not None else None

if df is not None:
    # Get unique values for countries and salespersons
    countries = df["ShipCountry"].unique().tolist()
    salespersons = df["SalesPerson"].unique().tolist()

    # Add an option for selecting all countries and salespersons
    countries.insert(0, "All Countries")
    salespersons.insert(0, "All Salespersons")

    # Dropdown for selecting country and/or salesperson
    selected_country = st.selectbox("Select Ship Country", countries)
    selected_salesperson = st.selectbox("Select Salesperson", salespersons)

    # Call the function to filter data based on user selection
    filtered_data = calculate_profit(selected_country if selected_country != "All Countries" else None,
                                     selected_salesperson if selected_salesperson != "All Salespersons" else None, df)

    # Show filtered data and dynamic graphs
    if filtered_data is not None:
        st.write("Filtered Data:")
        st.write(filtered_data)

        # Plot dynamic graphs
        if len(filtered_data) > 0:
            plot_dynamic_graph(filtered_data, "Unit_Sales_Price", selected_country)
            plot_dynamic_graph(filtered_data, "Unit_Cost", selected_country)
            plot_dynamic_graph(filtered_data, "Units_Sold", selected_country)
            plot_dynamic_graph(filtered_data, "Profit", selected_country)
        else:
            st.write("No data available for selected country and salesperson combination.")

# Check if data has changed and trigger rerun if necessary
if df is not None and last_data is not None:
    if not df.equals(last_data):
        st.rerun()
