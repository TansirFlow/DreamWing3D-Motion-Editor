import os
import xml.etree.ElementTree as xmlp

file = 'kick.xml'

robot_xml_root = xmlp.parse(file).getroot()
slots = []

for xml_slot in robot_xml_root:
    indices, angles = [], []
    for action in xml_slot:
        indices.append(int(action.attrib['id']))
        angles.append(float(action.attrib['angle']))
    delta_ms = float(xml_slot.attrib['delta'])
    slots.append((delta_ms, indices, angles))

s=""
for phase in slots:
    time=phase[0]
    s+=str(time)
    indices=phase[1]
    angles=phase[2]
    m={}
    for i in range(len(indices)):
        m[f"{indices[i]}"]=angles[i]
    for i in range(2,24):
        joint_id=f"{i}"
        if i in indices:
            angle=m[joint_id]
            s+=f" {angle}"
        else:
            s+=" 0"
    s+="\n"
print(s)
