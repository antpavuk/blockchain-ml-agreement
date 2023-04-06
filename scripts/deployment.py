import numpy as np
import pandas as pd
import statistics as st
from keras.models import Sequential
from keras.layers import Dense, LSTM
from brownie import AgreementContract, accounts


# Set random seed for reproducibility
np.random.seed(42)

# Get current Ether price in USD
ether_price = 2000


# Generate random transaction history for a party
def generate_transaction_history():
    num_transactions = 1000
    transaction_amounts = np.random.normal(loc=150, scale=50, size=num_transactions)
    transaction_amounts = np.clip(transaction_amounts, 0, None)

    transaction_dates = pd.date_range(start='2020-01-01', periods=num_transactions, freq='D')

    transaction_history = pd.DataFrame({
        'amount': transaction_amounts,
        'date': transaction_dates
    })

    return transaction_history


# Convert transaction amounts to Ether units
def convert_to_ether(transaction_history):
    mean = transaction_history['amount'].mean()
    std = transaction_history['amount'].std()
    ether_unit = ether_price / mean
    transaction_history['amount_normalized'] = transaction_history['amount'] * ether_unit
    return transaction_history, ether_unit


# Split data into train and test sets
def split_data():
    transaction_history, ether_unit = convert_to_ether(generate_transaction_history())
    train_size = int(len(transaction_history) * 0.8)
    train_data = transaction_history.iloc[0:train_size, :]
    test_data = transaction_history.iloc[train_size:len(transaction_history), :]
    return train_data, test_data, ether_unit


# Define function to create LSTM model
def create_lstm_model(train_data):
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=(1, 1)))
    model.add(LSTM(units=50))
    model.add(Dense(1))
    model.compile(loss='mean_squared_error', optimizer='adam')
    model.fit(train_data, train_data, epochs=100,
              batch_size=1, verbose=2)
    return model


def get_prediction_transaction_amount_mean():
    # Train LSTM model on transaction history
    train_data, test_data, ether_unit = split_data()

    train_data_lstm = np.array(train_data['amount_normalized']).reshape(-1, 1, 1)
    lstm_model = create_lstm_model(train_data_lstm)

    # Evaluate model on test data
    test_data_lstm = np.array(test_data['amount_normalized']).reshape(-1, 1, 1)
    predictions = lstm_model.predict(test_data_lstm)
    predictions = predictions.reshape(-1) / ether_unit

    predicted_transaction_amount_mean = st.mean(predictions)


    # Print results
    print('Actual Transaction Amounts (in Ether):')
    print(test_data['amount'].values)
    print('Predicted Transaction Amount Mean (in Ether):')
    print(predicted_transaction_amount_mean)
    return predicted_transaction_amount_mean


def get_prediction_transaction_amount_mean_for_parties():
    predicted_transaction_amount_mean_party_a = get_prediction_transaction_amount_mean()
    predicted_transaction_amount_mean_party_b = get_prediction_transaction_amount_mean()

    return predicted_transaction_amount_mean_party_a, predicted_transaction_amount_mean_party_b


def deploy_contract(party_a, party_b, contract_value, contract_duration, party_a_next_transaction_mean, party_b_next_transaction_mean):
    # Set the account that will deploy the contract
    deployer_account = accounts[0]

    # Deploy the contract with the specified arguments
    agreement_contract = AgreementContract.deploy(
        party_a,
        party_b,
        contract_value,
        contract_duration,
        party_a_next_transaction_mean,
        party_b_next_transaction_mean,
        {'from': deployer_account}
    )

    # Print the contract address for reference
    print(f"AgreementContract deployed at: {agreement_contract.address}")

    return agreement_contract

def main():

    # Specify the parties and contract details
    party_a = accounts[1]
    party_b = accounts[2]
    fund_lender = accounts[3]
    fund_lender_2 = accounts[4]
    fund_lender_3 = accounts[5]
    fund_lender_4 = accounts[6]
    contract_value = "100 ether"
    contract_duration = 86400 # 1 day in seconds

    party_a_next_transaction_mean, party_b_next_transaction_mean = get_prediction_transaction_amount_mean_for_parties()
    print(party_a_next_transaction_mean, 'party_a_next_transaction_mean')
    print(party_b_next_transaction_mean, 'party_b_next_transaction_mean')

    fund_lender.transfer(party_a, contract_value)
    fund_lender_2.transfer(party_b, contract_value)
    fund_lender_3.transfer(party_a, contract_value)
    fund_lender_4.transfer(party_b, contract_value)

    print(party_a.balance(), 'party_a.balance')
    print(party_b.balance(), '2 party_b.balance')

    # Deploy the contract
    agreement_contract = deploy_contract(party_a, party_b, contract_value, contract_duration, f"{party_a_next_transaction_mean} ether", f"{party_b_next_transaction_mean} ether")

    print('Before confirm')
    print(agreement_contract.partyAConfirmed(), 'agreement_contract.partyAConfirmed()')
    print(agreement_contract.partyBConfirmed(), 'agreement_contract.partyBConfirmed()')

    # Confirm the agreement as party A
    agreement_contract.confirmAgreement({'from': party_a, 'value': contract_value})

    # Confirm the agreement as party B
    agreement_contract.confirmAgreement({'from': party_b, 'value': contract_value})

    print(agreement_contract.partyA(), 'agreement_contract.partyA()')
    print(agreement_contract.partyB(), 'agreement_contract.partyB()')
    print(agreement_contract.contractValue(), 'agreement_contract.contractValue()')
    print(agreement_contract.contractExpirationDate(), 'agreement_contract.contractExpirationDate()')
    print('balance of contract', agreement_contract.balance(), 'agreement_contract.balance()')
