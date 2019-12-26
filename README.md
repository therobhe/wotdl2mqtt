# WoTDL Ontology to AsyncAPI

## Overview
This adaption of the [WoTDL2API](https://github.com/heseba/wotdl2api) API Generation Toolchain introduces an MQTT extended version of the [WoTDL OWL Ontology](https://vsr.informatik.tu-chemnitz.de/projects/2019/growth/wotdl/wotdl.owl) Ontology in order to enable MQTT communication patterns.

It uses a model-to-model transformation to generate an [AsyncAPI](https://www.asyncapi.com/) specification. 
The Flask-based AsyncAPI is generated through a developed code generator within 02_asyncAPI_codegen.py The model-to-text generation uses the [Flask-MQTT extension](https://github.com/stlehmann/Flask-MQTT) in combination with the [Eclipse Mosquitto broker](https://github.com/eclipse/mosquitto) for enabling communicaiton between IoT devices of a smart home test setting.

## Requirements
- Python 3.7.0+
- for python requirements see requirements.txt

## Usage
Get the dependencies:
```
pip install -r requirements.txt
```

Adapt the IN variable within the following file to point to an ontology instance and run the model-to-model transformation:

```
python 01_m2m_asyncapi.py
```

Run the model-to-text generation:

```
python 02_asyncAPI_code_generator
```

