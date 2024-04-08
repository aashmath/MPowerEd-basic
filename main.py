
import os
import threading
import cv2
from PIL import Image, ImageTk
from flask import Flask, redirect, url_for, render_template, request, send_file, jsonify, session
import os
import re
from gtts import gTTS


from IPython.display import display, Javascript
from base64 import b64decode
import json

from google.api_core.client_options import ClientOptions
from google.cloud import vision
from google.cloud.vision_v1 import types
from googletrans import Translator
from google.cloud import speech



import requests


os.environ['OPENAI_API_KEY'] = "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"





app = Flask(__name__, template_folder='templates',static_folder='static')


# Define Flask routes
@app.route("/")
def index():
    return render_template("index.html")


# Get Image from html
@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' in request.files:
        image = request.files['image']
        image.save('captured_image.png')  # Specify the desired save location
        print ( 'Image uploaded successfully!')
        return 'Image uploaded successfully!'
        #return render_template('index.html')
    else:
        print ( 'No image provided.')
        return 'No image provided.'
        #return render_template('index.html')

# Convert saved image to Text (from <Get Text> button)
@app.route('/image_to_text', methods=['POST'])
def image_to_text():
    img=Image.open('captured_image.png')
    img = img.resize((250, 200), Image.LANCZOS)  # Resize it
    img.save('scan1.jpg', format='JPEG')  # Save the resized image
    print ("image is: ", img)
    path = "scan1.jpg"

    options = ClientOptions(api_key="AIzaSyDhM79PWiy6eG9xlI7KbCEffZXxhyJ4JZI")

    client = vision.ImageAnnotatorClient(client_options=options)
    print ("client is", client)
    with open(path, 'rb') as image_file:
        content = image_file.read()
        image = cv2.imread(path)
        _, encoded_image = cv2.imencode('.jpg', image)
        content_cv2 = encoded_image.tobytes()
        image_cv2 = types.Image(content=content_cv2)


    response = client.text_detection(image=image_cv2)
    if not response:
        return jsonify("null")

    texts = response.text_annotations


    text = texts[0].description
    print ("Language is: --------------------------",texts[0].locale)
    print ("text is: --------------------", text)
    #return jsonify(text)
    processed_text = text
    #return  processed_text
    return jsonify(text)


# Create a function to convert the text to speech using gTTS and playsound
@app.route('/text_to_speech', methods=['POST'])
def text_to_speech():
    print ("here..................")
    data = request.get_json()
    text = data.get('final_text')
    print ("text for audio is",text)

    # DetectLanguage fails when text is only numericals and special chars, so adding an english string
    if (bool(re.match('^[0-9!@#$%^&*_+|~=`\\s{}\[\]:";\'<>?,.\/]*$', text))):
        text = "what is " + text


    translator = Translator()
    detected_language = translator.detect(text)
    text_language = detected_language.lang

    print("single_detection lang is ",text_language)


    SCANNED_LANG = text_language
    tts = gTTS(text=text, lang=text_language)

    # Save the speech as an MP3 file
    filename = "static/speech.mp3"


    tts.save(filename)

    return send_file(filename, mimetype='audio/mp3')


# Create a function to translate the text
@app.route('/translate', methods=['POST'])
def translate():
    print ("here1................")
    data = request.get_json()
    text = data.get('final_text')
    lang = data.get('trans_lang')

    print ("text is", text)
    print ("new lang is", lang)


    translator = Translator()
    detected_language = translator.detect(text)

    print(f"The detected language is: {detected_language.lang}")



    TRANSLATED_TEXT = translator.translate(text, src=detected_language.lang, dest=lang)



    print ("Translated text is", TRANSLATED_TEXT.text)
    return jsonify(TRANSLATED_TEXT.text)



@app.route('/explain', methods=['POST'])
def explain():
    import openai
    from openai import ChatCompletion


    api_key = os.environ.get("OPENAI_API_KEY")

    data = request.get_json()
    text = data.get('final_text')
    lang = data.get('trans_lang')
    print ("text to explain is", text)
    print ("lang given is", lang)

    if data.get('trans_lang'):
        target = data.get('trans_lang')
    else:
        target = "en"


    messages = [ {"role": "system", "content":
                  "You are a intelligent assistant."} ]
    message = "Explain and summarize in easy language terminology"+data.get('final_text')

    if message:
        messages.append( {"role": "user", "content": message}, )

        chat = openai.ChatCompletion.create( model="gpt-3.5-turbo", messages=messages )

    expl_text = chat.choices[0].message.content

    translator = Translator()
    detected_language = translator.detect(expl_text)

    trans_expl_text = translator.translate(expl_text, src=detected_language.lang, dest=target)


    d ={
    'expl_text':expl_text,
    'trans_expl_text':trans_expl_text.text,
    }
    return json.dumps(d)


@app.route('/testq', methods=['POST'])
def testq():

    context = request.get_json()

    print ("context is:  ", context)
    # Replace with your actual OpExams API key
    API_KEY = "5JGN0qFUIvJPg5NXfpLyQE8HjkL6hsF"

    # API endpoint for OpExams Questions Generator
    API_ENDPOINT = "https://api.opexams.com/questions-generator"


    # Define the parameters for question generation
    request_body = {
        "type": "contextBased",  # Can be "contextBased" or "topicBased"
        "context": context,
        "questionType": "MCQ",  # Can be "MCQ", "TF", or "open"
        "language": "Auto",  # Optional: Language of generated questions (default is "Auto")
        "difficulty": "medium",  # Optional: Difficulty level ("easy", "medium", or "hard")
    }

    # Make the API request
    headers = {"api-key": API_KEY, "request-type":"test"}
  #  headers = {"api-key": API_KEY}
    response = requests.post(API_ENDPOINT, json=request_body, headers=headers)



    # Process the response
    if response.status_code == 200:
        data = response.json().get("data", [])
        print ("data is: ", data)
        for row in data:
            print (row,"\n")
            print(f"Question: {row['question']}")
            print(f"Answer: {row['answer']}")
            print(f"Options: {', '.join(row['options'])}\n")
    else:
        print(f"Error fetching questions. Status code: {response.status_code}")
    return json.dumps(data)

#-------------------------------------------------------------------
@app.route('/speech_to_text', methods=['POST'])
def speech_to_text():
    print (request)

    if 'audio_data' in request.files:
      # Get the audio file from the request
      audio_file = request.files['audio_data']

      audio_lang = request.form.get('audio_lang')



      print ("audio_lang is: ", audio_lang)

      filename = audio_file.filename + ".wav"
      # Save the audio file to the specified directory
      audio_file_path = os.path.join('.', filename)
      audio_file.save(audio_file_path)

      '''
      api_key = os.environ.get("OPENAI_API_KEY")
      if api_key is None:
          raise ValueError("Please set the OPENAI_API_KEY environment variable")
      '''
      client = speech.SpeechClient.from_service_account_file('keyfile.json')

      with open(filename, "rb") as audio_file:
          content = audio_file.read()

      # Create recognition audio object
      audio = speech.RecognitionAudio(content=content)

      # Specify alternative languages (e.g., English, Spanish, French)
      alternative_language_codes =['hi-IN', 'bn-IN', 'te-IN', 'mr-IN', 'ta-IN',
    'gu-IN', 'kn-IN']

      config = speech.RecognitionConfig(
          encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16, sample_rate_hertz=48000,language_code=audio_lang)

      # Perform speech recognition
      response = client.recognize(config=config, audio=audio)

      print ("reponse is ",response)

      # Print the transcribed text
      for result in response.results:
          print("Transcript: {}".format(result.alternatives[0].transcript))
          print("Language Code:  {}".format(result.language_code))
      return result.alternatives[0].transcript
    else:
        return 'No audio data received'



if __name__ == "__main__":
    app.run()
# Start the Flask server in a new thread
#threading.Thread(target=app.run, kwargs={"use_reloader": False}).start()
