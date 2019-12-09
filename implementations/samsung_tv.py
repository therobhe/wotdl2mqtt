from flask import Response

print('samsungTV imported')

def switch_on_tv(path_param, power):
    print("TV is on")
    #return Response(path_param + str(power), status=200)

def switch_off_tv():
    print("TV is off")
    #return Response('Running', status=200)