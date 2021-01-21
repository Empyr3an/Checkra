import numpy as np

def get_algo_timestamps(one_topic_confi): #returns array of long chains of topics after smoothing
    stream_data = []
    i, start, count = 0,0,0
    while i<len(one_topic_confi)-1: #collect length of same topics that occur together
        cur_topic = one_topic_confi[i][0]
        if cur_topic ==one_topic_confi[i+1][0]: #if same as previous topic
            count+=1
        else:
            stream_data.append([cur_topic, count, [start, i]]) #if not same, start new chain
            count=0
            cur_topic=one_topic_confi[i+1][0]
            start = i+1
        i+=1


    stream_data = [i for i in stream_data if i[1]>(len(one_topic_confi)/80)] # filters out small topic chains to avoid noise as 1.25% of total length of doc
    i = 0
    stream_data[0][2][0] = 0 #make first topic go from beginning of podcast
    while i<len(stream_data)-1: #adjusts topic boundaries to fill in cleared spaced
        if stream_data[i][2][1] !=stream_data[i+1][2][0]-1:
#             print(stream_data[i], stream_data[i+1])
            newcenter = (stream_data[i][2][1] + stream_data[i+1][2][0])//2
            move_up = newcenter - stream_data[i][2][1]
#             print("up", move_up)

            stream_data[i][2][1] += move_up
            stream_data[i][1] +=move_up

            move_down = stream_data[i+1][2][0] - newcenter-1
#             print("move_down", move_down)
            stream_data[i+1][2][0]-= move_down
            stream_data[i+1][1]+=move_down
        i+=1
    stamps = [[i[2][0], i[0]] for i in stream_data] #keep only first sentence marker and topic
    return np.array(stamps).astype(int).tolist()

