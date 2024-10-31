import requests
import boto3
import mysql.connector
from mysql.connector import Error
import time


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36'
}
MONTHS=["January","February","March","April","May","June","July","August","September","October","November","December"]
AWS_REGION = "AWS REGION"  
SNS_TOPIC_ARN = "SNS TOPIC ARN"
OUTPUT=[]
DB_HOST=""
DB_NAME=""         
DB_USER=""          
DB_PASS=""  
sns_client = boto3.client('sns', region_name=AWS_REGION)


class My_chess_apllication():
    def __init__(self):
        self.total_games=0

    def fetch_games_for_month(self,username, year, month):
        url = f'https://api.chess.com/pub/player/{username}/games/{year}/{month:02d}'
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            return response.json().get('games', [])
        else:
            print(f"Failed to fetch games for {year}-{month:02d}: {response.status_code}")
            return []
        
    def create_match_links(self,user_name,year,min_accuracy):
        for month in range(12):
            games=self.fetch_games_for_month(user_name,year,month+1)
            self.total_games+=len(games)
            print(f"fetching your games in {MONTHS[month]}")
            for game in games:
                accuracies=game.get('accuracies', {})
                white_accuracy=accuracies.get('white')
                black_accuracy=accuracies.get('black')
                pgn=game.get('pgn')
                start="https://www.chess.com/game/live/"
                end="]"
            
                if white_accuracy!=None and black_accuracy!=None:
                    if white_accuracy>=min_accuracy or black_accuracy>=min_accuracy:
                        start_index=pgn.find(start)
                        end_index=pgn.find(end, start_index)
                        game_url=pgn[start_index:end_index-1]
                        OUTPUT.append(f"White Accuracy: {white_accuracy}, Black Accuracy: {black_accuracy}\nGame URL: {game_url}")
            OUTPUT.append(f"Total Number of games played in {MONTHS[month]}: {len(games)}")
        OUTPUT.append(f"\nYOU PLAYED {self.total_games} games in {year}.")

    def subscribe_email(self,email):
        response = sns_client.subscribe(
            TopicArn=SNS_TOPIC_ARN,
            Protocol='email',
            Endpoint=email
        )
        subscription_arn = response['SubscriptionArn']
        print(f"Subscription ARN: {subscription_arn}. Please confirm the subscription in your email in 1 min.")
        time.sleep(20)
        return subscription_arn
        
    def send_sns_notification(self,email_content):
        response = sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=email_content,
            Subject="Chess.com Game Links with Accuracy Filter"
        )
        print("Notification sent:", response['MessageId'])

    def unsubscribe_email(self,email):
        response = sns_client.list_subscriptions_by_topic(TopicArn=SNS_TOPIC_ARN)
        for subscription in response['Subscriptions']:
            if subscription['Endpoint'] == email:
                subscription_arn = subscription['SubscriptionArn']
                sns_client.unsubscribe(SubscriptionArn=subscription_arn)
                print(f"Unsubscribed {email} successfully.")
            
    def connect_to_db(self):
        try:
            connection=mysql.connector.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASS
            )
            if connection.is_connected():
                return connection
        except Error as e:
            print(f"Failed to connect to the database: {e}")
            return None

    def insert_user(self,chess_username, email):
        connection=self.connect_to_db()
        if connection:
            try:
                cursor=connection.cursor()
                insert_query="""INSERT INTO chess_users (chess_username, email) VALUES (%s, %s);"""
                cursor.execute(insert_query, (chess_username, email))
                connection.commit()
                print("Data inserted successfully.")
            except Error as e:
                print(f"Error while inserting data: {e}")
            finally:
                cursor.close()
                connection.close() 

user_name=input("ENTER YOUR CHESS.COM USERNAME CORRECTLY: ")
user_mail=input("ENTER THE EMAIL TO RECEIVE GAME LINKS: ")
year=int(input("ENTER THE YEAR YOU WANT TO SEARCH: "))
min_accuracy=int(input("ENTER THE MINIMUM ACCURACY OF GAMES YOU WANT: ")) 
my_obj=My_chess_apllication()
my_obj.create_match_links(user_name,year,min_accuracy)
if OUTPUT:
    email_content=f"Chess.com Games for {user_name} with Minimum Accuracy {min_accuracy}:\n\n" + "\n\n".join(OUTPUT)
    subscription_arn=my_obj.subscribe_email(user_mail)
    my_obj.send_sns_notification(email_content)
    time.sleep(10)
    my_obj.unsubscribe_email(user_mail)

