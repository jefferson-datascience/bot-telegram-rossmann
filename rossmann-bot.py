import os
import pandas as pd
import json
import requests

from flask import Flask, request, Response

# constants
token = '5659695846:AAHtDPrh2Dkz76m1mA1PyCJn0Sviaxs7O5E'

# Indo about the bot
#https://api.telegram.org/bot5659695846:AAHtDPrh2Dkz76m1mA1PyCJn0Sviaxs7O5E/getMe
        
# Get Updates
#https://api.telegram.org/bot5659695846:AAHtDPrh2Dkz76m1mA1PyCJn0Sviaxs7O5E/getUpdates

# Webhook
#https://api.telegram.org/bot5659695846:AAHtDPrh2Dkz76m1mA1PyCJn0Sviaxs7O5E/setWebhook?url=https://bot-rossmann-prediction.herokuapp.com

# Send Messages
#https://api.telegram.org/bot5659695846:AAHtDPrh2Dkz76m1mA1PyCJn0Sviaxs7O5E/sendMessage?chat_id=938254555&text=Fala Neguim!


def send_message(chat_id, text):
    
    
    url = 'https://api.telegram.org/bot{}/'.format(token)
    url = url + 'sendMessage?chat_id={}'.format(chat_id)
    
    r = requests.post(url, json={'text':text})
    
    print('Status Code: {}'.format(r.status_code))
          
    return None
                

def load_dataset(store_id):
    
    # load dos dados de teste
    df10 = pd.read_csv('test.csv')
    df_store_raw = pd.read_csv('store.csv')


    # merge do dataset test + df_store_raw
    df_test = pd.merge(df10, df_store_raw, how='left', on='Store')

    # escolha de um store para predição
    df_test = df_test[df_test['Store'] == store_id]
          
    if not df_test.empty:

        # removendo os dias em que a loja está fechada.
        df_test = df_test[df_test['Open'] != 0]
        df_test = df_test[~df_test['Open'].isnull()]
        df_test = df_test.drop(columns='Id', axis=1)

        # convert Dataframe to json
        data = json.dumps(df_test.to_dict( orient='records'))
    
    else:
        data = 'error'

    return data


def predict(data):

    # Api Call
    url    = 'https://rossmann-predict-webapp.onrender.com/rossmann/predict'
    header = {'Content-type':'application/json'}
    data   = data

    r = requests.post(url, data = data, headers=header)
    print('Status Code: {}'.format(r.status_code))

    d1 = pd.DataFrame(r.json(), columns = r.json()[0].keys())
    
    return d1
          
          
def parse_message(message):
    
    chat_id = message['message']['chat']['id']
    store_id = message['message']['text']
          
    store_id = store_id.replace('/', '')
          
    try:
        store_id = int(store_id)
          
    except ValueError: 
        store_id = 'error'
              
    return chat_id, store_id


# API Inicializado          
app = Flask(__name__)
          
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        message = request.get_json()

        chat_id, store_id = parse_message(message)

        if store_id != 'error':
            
            aviso = 'Processando a predição das próximas 6 semanas de vendas da loja {}.'.format(store_id)
            send_message(chat_id, aviso)    
            
            #loading data
            data = load_dataset(store_id)

            if data != 'error':

                #Prediction
                d1 = predict(data)

                #Calculation
                d2 = d1[['store', 'prediction']].groupby('store').sum().reset_index()    

                #send message
                msg = 'A loja {} vai vender nas próximas 6 semanas R$ {:,.2f}'.format(d2['store'].values[0], d2['prediction'].values[0])
                send_message(chat_id, msg)
                return Response('Ok', status='200')

            else:
                aviso_2 = 'Não há dados disponíveis sobre a loja {} para a previsão de vendas das próximas 6 semanas.'.format(store_id)
                send_message(chat_id, aviso_2)
                return Response('Ok', status='200')
            
        else:
            send_message(chat_id, 'ID da loja inválido. Digite um ID válido, por favor.')
            return Response('OK', status='200')      

    else:
        return '<h1>Rossmann Telegram Bot</h1>'
          
          
if __name__=='__main__':
    
    port = os.environ.get('PORT', '5000')
    app.run(host='0.0.0.0', port=port)


    