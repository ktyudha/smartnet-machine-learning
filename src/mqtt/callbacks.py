def on_connect(client, userdata, flags, rc):
    print("Connected")


def on_message(client, userdata, msg):
    print(msg.topic)
    print(msg.payload.decode())

# SOON
# def on_message(...):
#     payload = parse_payload(...)
#     feature = preprocess(payload)
#     prediction = predict(feature)
#     relay = decide(prediction)
#     publish(relay)