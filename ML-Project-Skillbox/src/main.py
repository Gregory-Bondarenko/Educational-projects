import pandas as pd
import pickle

columns_encoders = []
path = 'encoders/'
cols_to_encode = [
    'utm_source',
    'utm_medium',
    'utm_campaign',
    'utm_adcontent',
    'device_category',
    'device_brand',
    'device_browser',
    'geo_country',
    'geo_city']


for col in cols_to_encode:
    with open(f"c:\Users\Gregory\proga\Final_project\ml-project-skillbox{path}{col}_encoder.pickle", "rb") as f:
        d = pickle.load(f)
        columns_encoders.append(d)

def main():
    with open("c:\Users\Gregory\proga\Final_project\ml-project-skillboxmodel.pickle", "rb") as f:
        model = pickle.load(f)

    run = True
    while run:
        print()
        user_info = get_user_info()
        
        prediction = model.predict(user_info)
        print("Prediction: ", end='')

        if prediction == 1:
            print("Пользователь совершит целевое действие\n")
        else:
            print("Пользователь НЕ совершит целевое действие\n")

        print("Желаете ввести информацию о другом пользователе?")
        if input("Введите да/нет: ") == "да": continue
        else: run = False


def model_predict(model, input_layer):
    model.predict(input_layer)

def get_user_info():
    COLUMNS_NAMES = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_adcontent',
       'device_category', 'device_brand', 'device_screen_resolution',
       'device_browser', 'geo_country', 'geo_city']
    
    print("Пожалуйста введите данные пользователя\n")
    info = []

    for i, col in enumerate(COLUMNS_NAMES):
        okey = False

        while not(okey):
            okey = True
            cell_value = input(f"Значение поля {col}: ").strip()

            if i < 6:
                if cell_value in columns_encoders[i].keys():
                    info.append(columns_encoders[i][cell_value])
                else:
                    info.append(-1)
            elif i == 6:
                try:
                    a, b = cell_value.split("x")
                    s = int(a) * int(b)
                    info.append(int(s))
                except:
                    print("Введено неверное значение! Попробуйте еще раз.\n")
                    okey = False
            else:
                if cell_value in columns_encoders[i-1].keys():
                    info.append(columns_encoders[i-1][cell_value])
                else:
                    info.append(-1)
            
    print()
    return info

if __name__ == '__main__':
    main()
