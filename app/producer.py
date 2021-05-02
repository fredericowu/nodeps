from time import sleep
from json import dumps
from kafka import KafkaProducer


#producer = KafkaProducer(bootstrap_servers=['kafka:9092'])

producer = KafkaProducer(bootstrap_servers=['kafka:9092'],
                         value_serializer=lambda x:
                         dumps(x).encode('utf-8'))

for e in range(1):
    data = {'number': e}
    #data = "producer"
    future = producer.send('numtest', value=data)
    #future.get(timeout=60)
    print("enviado")
    #sleep(5)

producer.flush()


"""


msg = ('kafkakafkakafka' * 20).encode()[:100]
size = 1000000
producer = KafkaProducer(bootstrap_servers='localhost:9092')

def kafka_python_producer_sync(producer, size):
    for _ in range(size):
        future = producer.send('topic1', msg)
        result = future.get(timeout=60)
    producer.flush()
    
def success(metadata):
    print(metadata.topic1)

def error(exception):
    print(exception)

def kafka_python_producer_async(producer, size):
    for _ in range(size):
        print("send "+str(_))
        producer.send('topic1', msg).add_callback(success).add_errback(error)
    producer.flush()



#kafka_python_producer_sync(producer, 5)
kafka_python_producer_async(producer, 10)

"""