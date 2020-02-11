# Pivot fire starter
import os
import errno
import uuid
import json
import datetime

import xml.dom.minidom as md

from string import Template

user = ''
password = ''
commands = ''
devices = ''
feedback = ''
links = ''
locations = ''
connections = ''
lightingdevices = ''
curtaindevices = ''
producer = ''
icon = ''
category = ''
network_open_sequence = ''
keypad_id = 0

def get_json(project):
    with open(project) as conf:
        jsonfile = json.load(conf)
    return jsonfile


def make_path(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


def new_prettify(content):
    reparsed = md.parseString(content)

    return '\n'.join([line for line in reparsed.toprettyxml(indent=' ' * 2).split('\n') if line.strip()]).replace('$lf$', '&#13;&#10;')


def build_driver(commands, kind):
    with open('xml/template.xml') as file_input:
        template_src = Template(file_input.read())

        d = {
            'cmds': commands, 
            'date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
            'user': user, 
            'password': password,
            'devices': devices, 
            'fb':feedback, 
            'links': links,
            'producer': producer,
            'icon': icon,
            'cat': category,
            'network_open_sequence': network_open_sequence
            }

        result = template_src.substitute(d)
    with open('output/lutron_'+kind+'_driver.xml', 'w') as driver:
        driver.write(new_prettify(result))
        driver.close()


def build_areas_lighting():
    with open('xml/lighting.xml') as file_input:
        template_src = Template(file_input.read())

        d = {
            'locations': locations,
            'connections': connections,
            'devices': lightingdevices
            }

        result = template_src.substitute(d)
    with open('output/comfort_lighting.xml', 'w') as driver:
        driver.write(new_prettify(result))
        driver.close()


def build_areas_curtains():
    with open('xml/blinds.xml') as file_input:
        template_src = Template(file_input.read())

        d = {
            'locations': locations,
            'connections': connections,
            'devices': curtaindevices
            }

        result = template_src.substitute(d)
    with open('output/comfort_blinds.xml', 'w') as driver:
        driver.write(new_prettify(result))
        driver.close()


def parse_json_to_driver(jsonobj, kind):
    global commands
    global user
    global password 
    global feedback
    global devices
    global links
    global producer
    global icon
    global category
    global network_open_sequence
    global keypad_id

    network_open_sequence = ''

    feedback_no = 1;

    if kind == 'light':
        title = "Lights"
        icon = 'comfort_light'        
        producer = '<producer id="lightproducer"><products><product value="light"/></products></producer><port id="out"><products><product value="light"/></products></port><link from="lightproducer" to="out" />'
    else:
        title = "Curtains"
        icon = 'comfort_curtain'
        producer = '<producer id="curtainproducer"><products><product value="curtain"/></products></producer><port id="out"><products><product value="curtain"/></products></port><link from="curtainproducer" to="out" />'
    
    category = title

    commands = ''
    feedback = ''
    devices = ''
    links = ''
    seq = 3

    user = jsonobj['login']['user'] 
    password = jsonobj['login']['password']

    for level in jsonobj['levels']:
        for room in level['areas']:            
            keypad_id = 1

            prio_device = 1000
            prio = 900

            for keypad in room['keypads']:
                for button in keypad['buttons']:

                    network_open_sequence += ('<on-open_network_sequence_{0} value="?DEVICE,{1},{2},9"/>'.format(str(seq),keypad['integration-id'], button['id']+80))
                    seq += 1

                    commands+=('<keypad_{0}_{3}_btn_{2}_{1} value="#DEVICE,{0},{2},3$lf$#DEVICE,{0},{2},4"/>'.format(keypad['integration-id'], room['id'], button['id'], str(keypad_id)))
                    commands+=('<keypad_{0}_{3}_btn_{2}_{1}_start value="#DEVICE,{0},{2},3"/>'.format(keypad['integration-id'], room['id'], button['id'], str(keypad_id)))
                    commands+=('<keypad_{0}_{3}_btn_{2}_{1}_continue value="#DEVICE,{0},{2},5"/>'.format(keypad['integration-id'], room['id'], button['id'], str(keypad_id)))
                    commands+=('<keypad_{0}_{3}_btn_{2}_{1}_stop value="#DEVICE,{0},{2},4"/>'.format(keypad['integration-id'], room['id'], button['id'], str(keypad_id)))

                    feedback+='<feedback_'+str(feedback_no)+'_regex value="~DEVICE,'+str(keypad['integration-id'])+','+str(button['id']+80)+',9,([0-1])"/>'
                    feedback+='<feedback_'+str(feedback_no)+'_regex_detail value="keypad_'+str(keypad['integration-id'])+'_' + str(keypad_id) + '_btn_'+str(button['id'])+'_'+str(room['id'])+'"/>'
                    feedback_no += 1

                devices += '<!-- '+ room['label'] +' -->'
                devices += '<device id="keypad_' + str(keypad['integration-id']) + '_' + str(keypad_id) + '_' + str(room['id']+'"><category value="'+ title +'"/><priority value="'+str(prio_device)+'"/><state value="none"/><utility value="true"/><icon value="comfort_'+kind+'"/><settings>')
                for button in keypad['buttons']:
                    devices += '<trigger id="'+ str(button['id']) +'">'
                    devices += '<command value="keypad_'+str(keypad['integration-id'])+'_' + str(keypad_id) +'_btn_'+str(button['id'])+'_'+str(room['id'])+'"/>'
                    devices += '<label value="'+ button['label'] +'"/>'
                    devices += '<active>'
                    devices += '<legacy-condition detail="keypad_'+str(keypad['integration-id'])+'_' + str(keypad_id) +'_btn_'+str(button['id'])+'_'+str(room['id'])+'" equals="1"/>'
                    devices += '</active>'
                    devices += '<priority value="'+str(prio+prio_device)+'"/>'
                    devices += '<supports-startstop value="true"/>'
                    devices += '<general-tags>'
                    devices += '<tag>group:'+keypad['group']+'</tag>'
                    devices += '<tag>group_icon:comfort_group_'+kind+'</tag>'
                    devices += '<tag>master</tag>'
                    devices += '</general-tags>'
                    devices += '<products><product value="'+kind+'"/></products>'
                    devices += '</trigger>'
                    prio -= 10
                devices += '</settings><components><port id="in"><products><product value="'+kind+'"/></products></port><port id="out"><products><product value="'+kind+'"/></products></port><link from="in" to="out"/></components>'
                devices += '</device>'
                keypad_id += 1
                prio_device -= 100

            keypad_id = 1
            for keypad in room['keypads']:
                links += '<link from ="out" to="keypad_' + str(keypad['integration-id']) +'_' + str(keypad_id) + '_' + str(room['id'])+'.in"/>'
                keypad_id += 1


def parse_json_to_lighting_area(jsonobj):
    global locations
    global connections
    global lightingdevices

    connections = ''

    locations = "<locations>"
    for level in jsonobj['levels']:
        locations += '<level id=\"' + level['id'] + '\"><areas>'
        for room in level['areas']:
            locations += '<area id=\"' + room['id'] + '\">'
            locations += '<zones><zone id="main"><devices>'
            keypad_id=1
            for keypad in room['keypads']:
                locations += '<device value="lighting.keypad_' + str(keypad['integration-id']) + '_' + str(keypad_id) + '_' + str(room['id'])+'"/>'
                locations += '<device value="lighting'+ str(keypad['integration-id']) +'_' + str(keypad_id) + '-' + str(room['id']) + '"/>'
                connections += '<connection port="keypad_' + str(keypad['integration-id']) + '_' + str(keypad_id) + '_' + str(room['id'])+'.out" targetdevice="lighting'+ str(keypad['integration-id']) +'_' + str(keypad_id) + '-' + str(room['id']) + '" targetport="in"/>'
                lightingdevices += '<device id="lighting'+ str(keypad['integration-id']) +'_' + str(keypad_id) + '-' + str(room['id']) + '"><prototype value="generic:light:1"/><label value="Lighting"/></device>'
                keypad_id += 1
            locations += '</devices></zone></zones>'
            locations += '</area>'
            if 'slave' in room:
                locations += '<area id=\"' + room['slave'] + '\">'
                locations += '<zones><zone id="main"><devices>'
                keypad_id=1
                for keypad in room['keypads']:
                    locations += '<device value="lighting.keypad_' + str(keypad['integration-id']) + '_' + str(keypad_id) + '_' + str(room['id'])+'"/>'
                    locations += '<device value="lighting'+ str(keypad['integration-id']) +'_' + str(keypad_id) + '-' + str(room['slave']) + '"/>'
                    connections += '<connection port="keypad_' + str(keypad['integration-id']) + '_' + str(keypad_id) + '_' + str(room['id'])+'.out" targetdevice="lighting'+ str(keypad['integration-id']) +'_' + str(keypad_id) + '-' + str(room['slave']) + '" targetport="in"/>'
                    lightingdevices += '<device id="lighting'+ str(keypad['integration-id']) +'_' + str(keypad_id) + '-' + str(room['slave']) + '"><prototype value="generic:light:1"/><label value="Lighting"/></device>'
                    keypad_id += 1
                locations += '</devices></zone></zones>'
                locations += '</area>'

        locations += '</areas></level>'
    locations += '</locations>'


def parse_json_to_curtain_area(jsonobj):
    global locations
    global connections
    global curtaindevices

    connections = ''

    locations = "<locations>"
    for level in jsonobj['levels']:
        locations += '<level id=\"' + level['id'] + '\"><areas>'
        for room in level['areas']:
            locations += '<area id=\"' + room['id'] + '\">'
            locations += '<zones><zone id="main"><devices>'
            keypad_id = 1
            for keypad in room['keypads']:
                locations += '<device value="blinds.keypad_' + str(keypad['integration-id']) +'_' + str(keypad_id) + '_' + str(room['id'])+'"/>'
                locations += '<device value="blinds'+ str(keypad['integration-id']) +'_' + str(keypad_id) +'-' + str(room['id']) + '"/>'
                connections += '<connection port="keypad_' + str(keypad['integration-id']) +'_' + str(keypad_id) + '_' + str(room['id'])+'.out" targetdevice="blinds'+ str(keypad['integration-id']) +'_' + str(keypad_id) +'-' + str(room['id']) + '" targetport="in"/>'
                curtaindevices += '<device id="blinds'+ str(keypad['integration-id']) +'_' + str(keypad_id) + '-' + str(room['id']) + '"><prototype value="generic:curtain:1"/><label value="Curtains"/></device>'
                keypad_id += 1
            locations += '</devices></zone></zones>'
            locations += '</area>'
            if 'slave' in room:
                locations += '<area id=\"' + room['slave'] + '\">'
                locations += '<zones><zone id="main"><devices>'
                keypad_id=1
                for keypad in room['keypads']:
                    locations += '<device value="blinds.keypad_' + str(keypad['integration-id']) +'_' + str(keypad_id) + '_' + str(room['id'])+'"/>'
                    locations += '<device value="blinds'+ str(keypad['integration-id']) +'_' + str(keypad_id) +'-' + str(room['slave']) + '"/>'
                    connections += '<connection port="keypad_' + str(keypad['integration-id']) +'_' + str(keypad_id) + '_' + str(room['id'])+'.out" targetdevice="blinds'+ str(keypad['integration-id']) +'_' + str(keypad_id) +'-' + str(room['slave']) + '" targetport="in"/>'
                    curtaindevices += '<device id="blinds'+ str(keypad['integration-id']) +'_' + str(keypad_id) + '-' + str(room['slave']) + '"><prototype value="generic:curtain:1"/><label value="Curtains"/></device>'
                    keypad_id += 1
                locations += '</devices></zone></zones>'
                locations += '</area>'

        locations += '</areas></level>'
    locations += '</locations>'


if __name__ == "__main__":
    working_dir = os.getcwd()
    jsonobject_lighting = get_json('config_lighting.json')
    jsonobject_blinds = get_json('config_blinds.json')
    
    make_path('output')

    parse_json_to_driver(jsonobject_lighting, 'light')
    build_driver(commands, 'lighting')
    parse_json_to_lighting_area(jsonobject_lighting)
    build_areas_lighting()


    parse_json_to_driver(jsonobject_blinds, 'curtain')
    build_driver(commands, 'blinds')
    parse_json_to_curtain_area(jsonobject_blinds)
    build_areas_curtains()


    print('Please check the systemid in lighting.xml and blinds.xml')
    print('done!')