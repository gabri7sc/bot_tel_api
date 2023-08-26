import pandas as pd
import requests
import json
import os

from flask import Flask, request, Response

# constants
TOKEN= '5852728055:AAFLdMnsRRQxsRDKqcECoDwb_fKJMPitl6M'

# bot info
#https://api.telegram.org/bot5852728055:AAFLdMnsRRQxsRDKqcECoDwb_fKJMPitl6M/getMe

# get updates
#https://api.telegram.org/bot5852728055:AAFLdMnsRRQxsRDKqcECoDwb_fKJMPitl6M/getUpdates

# send message
#https://api.telegram.org/bot5852728055:AAFLdMnsRRQxsRDKqcECoDwb_fKJMPitl6M/sendMessage?chat_id=1645268127&text=oi

# render
#https://api.telegram.org/bot5852728055:AAFLdMnsRRQxsRDKqcECoDwb_fKJMPitl6M/setWebhook?url=https://telegram-bot-api-9mto.onrender.com

def send_message( chat_id, text ):
    # send message
    url = f'https://api.telegram.org/bot{TOKEN}/'
    url = url + f"sendMessage?chat_id={chat_id}"
    
    r = requests.post(  url, json={'text': text } )
    print(f'Status Code {r.status_code}')

    return None

def load_dataset( store_id ):
    # loading test dataset
    df10 = pd.read_csv( 'test.csv' )
    df101 = pd.read_csv('store.csv')

    # merge datasets
    df_test = pd.merge( df10, df101, how='left', on='Store' )

    # choose store for prediction
    df_test = df_test[df_test['Store'] == store_id ] 

    if not df_test.empty:


        # cleaning
        df_test = df_test[df_test['Open'] == 1]
        df_test = df_test.drop( 'Id', axis=1 )

        # covent dataframe to json
        data = json.dumps( df_test.to_dict( orient='records' ) )
    else:
        data = 'error'
    return data

def predict( data ):

    # API call
    url = 'https://rossmann-api-ygde.onrender.com/rossmann/predict'

    header = {'Content-type': 'application/json' }
    data = data

    r = requests.post( url, data=data, headers=header )
    print(f'Status Code {r.status_code}')

    d1 = pd.DataFrame( r.json(), columns=r.json()[0].keys() )

    return d1

def parse_message( message ):
    chat_id = message['message']['chat']['id']
    store_id = message['message']['text']

    store_id = store_id.replace( '/', '' )
    
    try:
        store_id = int(store_id)

    except ValueError:
        store_id = 'error'
    return chat_id, store_id

# init api
app = Flask( __name__ )

@app.route( '/', methods=['GET', 'POST'] )
def index():
    if request.method == 'POST':
        message = request.get_json()
        chat_id, store_id = parse_message( message )

        if store_id != 'error':
            # loading data
            data = load_dataset( store_id )
            if data != 'error':

                # prediction
                d1 = predict( data )

                # calculation
                d2 = d1[['store', 'prediction']].groupby('store').sum().reset_index()
                
                # send message
                msg = 'Store number {} will sell R${:,.2f} in the next 6 weeks'.format(
                    d2['store'].values[0],
                    d2['prediction'].values[0] )

                send_message( chat_id, msg )
                return Response( 'Ok', status=200 )

            else:
                send_message( chat_id, 'Store ID is not Available' )
                return Response( 'Ok', status=200 )

        else:
            send_message( chat_id, 'Store ID is Wrong' )
            return Response( 'Ok', status=200 )
    else:
        return '<h1> Rossmann Telegram Bot </h1>'

if __name__ == '__main__':
    port = os.environ.get( 'PORT', 5000 )
    app.run ( host='0.0.0.0', port=port )