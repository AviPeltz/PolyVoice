from multiprocessing import Pipe, Process
from flask import Flask, request, make_response, jsonify
from wiki_downloader import get_answer
from wiki_daemon import run_daemon
import atexit

# initialize the flask app
app = Flask(__name__)


# default route
@app.route('/')
def index():
    return 'Hello World!'


# function for responses
def results():
    # build a request object
    req = request.get_json(force=True)

    # fetch action from json
    human_question = req.get('queryResult').get('queryText')

    qa_parent_conn.send(human_question)
    answer = qa_parent_conn.recv()

    # return a fulfillment response
    return {'fulfillmentText': answer}


# create a route for webhook
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    # return response
    return make_response(jsonify(results()))


def close_wiki_daemon(pipe, process):
    pipe.close()
    print("Waiting for child process to end")
    process.join()


# run the app
if __name__ == '__main__':
    qa_parent_conn, qa_child_conn = Pipe()
    wiki_daemon = Process(target=run_daemon, args=(qa_child_conn,))
    wiki_daemon.start()

    atexit.register(close_wiki_daemon, qa_parent_conn, wiki_daemon)

    app.run()
