from graphbrain.parsers import *
parser = create_parser(name='en')
text = "The Turing test, developed by Alan Turing in 1950, is a test of machine intelligence."

parses = parser.parse(text)
for parse in parses:
    edge = parse['main_edge']
    print(edge.to_str())