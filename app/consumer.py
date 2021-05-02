from kafka import KafkaConsumer
#from pymongo import MongoClient
from json import loads


#consumer = KafkaConsumer('numtest', bootstrap_servers=['localhost:9092'])
consumer = KafkaConsumer('numtest', bootstrap_servers='kafka:9092')
consumer.subscribe(['numtest'])

print("pronto")
for msg in consumer:
    print (msg)

print("finalizou")
exit(1)

consumer = KafkaConsumer(
    'numtest',
     bootstrap_servers=['localhost:9092'],
     #auto_offset_reset='earliestaaa',
     #enable_auto_commit=True,
     #group_id='my-group',
     #value_deserializer=lambda x: loads(x.decode('utf-8'))
)


#client = MongoClient('localhost:27017')
#collection = client.numtest.numtest


for message in consumer:
    message = message.value
    #collection.insert_one(message)
    print(message)
    #print('{} added to {}'.format(message, collection))




"""
from kafka import KafkaConsumer, TopicPartition

size = 1000000

consumer1 = KafkaConsumer(bootstrap_servers='localhost:9092')
def kafka_python_consumer1():
    consumer1.subscribe(['topic1'])
    for msg in consumer1:
      print("msg received")
      print(msg)


consumer2 = KafkaConsumer(bootstrap_servers='localhost:9092')
def kafka_python_consumer2():
    consumer2.assign([TopicPartition('topic1', 0), ])
    for msg in consumer2:
        print(msg)


consumer3 = KafkaConsumer(bootstrap_servers='localhost:9092')
def kafka_python_consumer3():
    partition = TopicPartition('topic3', 0)
    consumer3.assign([partition])
    last_offset = consumer3.end_offsets([partition])[partition]
    for msg in consumer3:
        if msg.offset == last_offset - 1:
            break



#kafka_python_consumer1()
kafka_python_consumer2()
"""