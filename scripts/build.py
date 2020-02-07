# Pivot fire starter
import os
import errno
import uuid
import json

import xml.dom.minidom as md
from string import Template


def prompt():
    projectname = ''
    projectnumber = 0
    systemid = ''
    jsonfile = ''

    while projectnumber == 0:
        projectnumber = input('Enter the project build number: ')
        if projectnumber == 0:
            print('You have to enter a project build number first')

    while not projectname:
        projectname = input('Enter the project name (leave blank if unknown): ')
        if not projectname:
            projectname = "Project " + str(projectnumber)

    while not systemid:
        systemid = input('Enter a unique system id (hit enter for random): ')
        if not systemid:
            systemid = str(uuid.uuid1())

    while not jsonfile:
        jsonfile = input("Provide the configuration file name (press enter to use project.json): ")
        if not jsonfile:
            jsonfile = "project.json"

    return [projectname, projectnumber, systemid, jsonfile]


def make_idoru_conf(path):
    with open(path + 'idoru.conf', 'w') as configfile:
        configfile.write('# This file contains settings for the Idoru System.\n')
        configfile.write('# -\n')
        configfile.write('# Format:\n')
        configfile.write('#   [variable name] = [variable value]\n')
        configfile.write('#\n\n\n')

        configfile.write('#can.provider = dummy\n')
        configfile.write('#can.provider = tcpbridge\n')
        configfile.write('#can.bridge.address = 192.168.0.100\n')
        configfile.write('#can.provider = tcpproxy\n')
        configfile.write('#can.proxy.address = 192.168.0.100\n')
        configfile.write('#can.proxy.port = 9000\n')

        configfile.write('can.bridge.port = 1200\n')
        configfile.write('can.heartbeat = true\n')
        configfile.write('core.system.filename = system.xml\n')
        configfile.write('core.users.filename = users.xml\n')
        configfile.write('core.system.path = system/\n')
        configfile.write('core.database.path = database/\n')
        configfile.write('core.users.path = users/\n')
        configfile.write('core.webroot.path = webroot/\n\n\n')

        configfile.write('remote.prcp.port = 8000\n')
        configfile.write('remote.gc.port = 4998\n\n\n')

        configfile.write('debug.dummydrivers = 0\n')
        configfile.write('debug.dummyprovider = 0\n')
        configfile.write('debug.print_detail_values = true\n\n')
        
        configfile.write('log.debug = false\n')
        configfile.write('log.verbose = 0\n')
        configfile.write('log.min_change_duration = 2000')

def make_gitignore(path):
    with open(path + '.gitignore', 'w') as gitignore:
        gitignore.write('.DS_Store\n')
        gitignore.write('.idea/\n')


def make_path(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


def make_project_directory(path, project_name):
    project_dir = path + '/../' + project_name[1] + '/'
    make_path(project_dir)
    return project_dir


def make_readme(path, project_name):
    with open(path + 'README.md', 'w') as readme:
        readme.write("#" + project_name[1] + " (" + project_name[0] + ") Pivot files\n")
        readme.write("##" + project_name[2] + "\n")
        readme.write("System and user files\n")
        readme.write("*Add information to this file as the project goes*")
        readme.close()


def make_dirs(path):
    pivot_dirs = ['info', 'system', 'users', 'webroot', 'webroot/images/area_images']
    for dir in pivot_dirs:
        make_path(path + dir)


def new_prettify(content):
    reparsed = md.parseString(content)
    return '\n'.join([line for line in reparsed.toprettyxml(indent=' ' * 2).split('\n') if line.strip()])


def make_area_xml(path, project, levelname, level, devices, areaname, areaid):
    with open("xml/area.xml") as file_input:
        template_src = Template(file_input.read())
        d = {'systemid': project[2], 'project_buildnr': project[0], 'locations': level, 'devices': devices}
        result = template_src.substitute(d)
        make_path(path + "system/" + levelname)

    if not areaid:
        print("Writing file: {0}".format("system/" + levelname + "/" + areaname['id'] + ".xml"))
        with open(path + "system/" + levelname + "/" + areaname['id'] + ".xml", 'w') as file_output:
            file_output.write(new_prettify(result))
            file_output.close()
    else:
        print("Writing file with room id: {0}".format("system/" + levelname + "/" + areaname['id'] + "_" + areaid + ".xml"))
        with open(path + "system/" + levelname + "/" + areaname['id'] + "_" + areaid + ".xml", 'w') as file_output:
            file_output.write(new_prettify(result))
            file_output.close()
            
def make_device_xml(file, area, prototype):
    with open("xml/" + file) as file_input:
        template_src = Template(file_input.read())
        d = {'areaname': area, 'prototype': prototype}
        result = template_src.substitute(d)
        return result


def make_root_user(path, allowed, project):
    with open("xml/users.xml") as file_input:
        template_src = Template(file_input.read())
        d = {'allowed': allowed, 'systemid': project[2]}
        result = template_src.substitute(d)
    with open(path + "users/users.xml", 'w') as usersfile:
        usersfile.write(new_prettify(result))
        usersfile.close()


def make_system_xml(path, areas_xml, project):
    areas = ""
    for xmlfile in areas_xml:
        if not xmlfile.startswith("<"):
            areas += "<merge include=\"" + xmlfile + "\"/>"
        else:
            areas += xmlfile

    with open("xml/system.xml") as file_input:
        template_src = Template(file_input.read())
        d = {'systemid': project[2], 'includes': areas, 'project_buildnr': project[0]}
        result = template_src.substitute(d)
    with open(path + "system/system.xml", 'w') as system_file:
        system_file.write(new_prettify(result))
        system_file.close()


def get_json(project):
    with open(project[3]) as conf:
        jsonfile = json.load(conf)
    return jsonfile


def build_location(levelprio, levelid, levellabel, roomobj, devices):
    file_input = open("xml/level.xml")
    template_src = Template(file_input.read())
    d = {'levelid': levelid, 'levellabel': levellabel, 'levelprio': levelprio, 'areaid': roomobj['id'],
         'arealabel': roomobj['label'],
         'areaicon': roomobj['icon'], 'area_major': roomobj['major'], 'area_minor': roomobj['minor'],
         'devices': devices}
    result = template_src.substitute(d)
    return result


def parse_json_to_xml(jsonobj, project, path):
    area_xmls = []
    root_allowed = "<allowed-locations>"
    for level in jsonobj['levels']:
        area_xmls.append("<!-- " + level['label'] + " -->")
        root_allowed += "<level id=\"" + level['id'] + "\"><areas>"
        for room in level['areas']:
            root_allowed += "<area id=\"" + room['id'] + "\"/>"
            devices_xml = ""
            devices_xml_short = ""
            if 'tv' in room:
                devices_xml += make_device_xml("tv.xml", room['id'], room['tv'])
                devices_xml_short += "<device value=\"tv-" + room['id'] + "\"/>"
            if 'speakers' in room:
                devices_xml += make_device_xml("speakers.xml", room['id'], room['speakers'])
                devices_xml_short += "<device value=\"speakers-" + room['id'] + "\"/>"
            if 'room_no' in room:
                room_no = room['room_no']
            else:
                room_no = ""

            location_xml = build_location(level['prio'], level['id'], level['label'], room, devices_xml_short)
            make_area_xml(path, project, level['id'], location_xml, devices_xml, room, room_no)

            if not room_no:
                area_xmls.append(level['id'] + "/" + room['id'] + ".xml")
            else:
                area_xmls.append(level['id'] + "/" + room['id'] + "_" + room_no + ".xml")           
        root_allowed += "</areas></level>"
    root_allowed += "</allowed-locations>"
    make_system_xml(path, area_xmls, project)
    make_root_user(path, root_allowed, project)


if __name__ == "__main__":
    working_dir = os.getcwd()
    print('\n _______  ___   __   __  _______  _______\n|       ||   | |  | |  ||       ||       |\n|    _  ||   | |  |_|  ||   _   ||_     _|\n\
|   |_| ||   | |       ||  | |  |  |   |\n|    ___||   | |       ||  |_|  |  |   |\n|   |    |   |  |     | |       |  |   |\n\
|___|    |___|   |___|  |_______|  |___|   \n\nPlease enter the details below\n\nREMEBER THAT EXISTING FILES IN THE PROJECT FOLDER MAY BE OVERWRITTEN! \n\n')

    project = prompt()
    project_dir = make_project_directory(working_dir, project)
    make_readme(project_dir, project)
    make_idoru_conf(project_dir)
    make_dirs(project_dir)
    make_gitignore(project_dir)
    jsonobject = get_json(project)
    print("\n")
    parse_json_to_xml(jsonobject, project, project_dir)
    print('\nDone with generating! :)\n\n')
