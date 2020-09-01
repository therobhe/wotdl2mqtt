# WoTDL Ontology to AsyncAPI

## Overview
This adaption of the [WoTDL2API](https://github.com/heseba/wotdl2api) toolchain includes an MQTT extended version of the [WoTDL OWL Ontology](https://vsr.informatik.tu-chemnitz.de/projects/2019/growth/wotdl/wotdl.owl) within mqttwotdl.ttl. 

Similar to WoTDL2API, instances of the MQTT enhanced ontology can be used to generate AsyncAPI specifications and is part of the GrOWTH approach for Goal-Oriented End User Development for Web of Things Devices. [1] 

It uses a model-to-model transformation to generate an [AsyncAPI](https://www.asyncapi.com/) specification. 
The Flask-based AsyncAPI is generated through the developed code generator within 02_asyncAPI_codegen.py.

## Requirements
- Python 3.7.0+
- for python requirements see requirements.txt

## Usage
Get the dependencies:
```
pip install -r requirements.txt
```

Adapt the IN variable to point to your ontology instance and run the model-to-model transformation:

```
python 01_m2m_asyncapi.py
```

Run the model-to-text generation:

```
./02_m2t_openapi_flask.sh
```
## Raspberry Pi Configuration
Read about the environment details this project was integrated into [here](https://docs.google.com/document/d/1OXGWPZJjqQrg9VodgYT9wRHfVMFTjsyXz5kDNvTUQwM/edit?usp=sharing)

## References

[1] Noura M., Heil S., Gaedke M. (2018) GrOWTH: Goal-Oriented End User Development for Web of Things Devices. In: Mikkonen T., Klamma R., Hernández J. (eds) Web Engineering. ICWE 2018. Lecture Notes in Computer Science, vol 10845. Springer, Cham

[2] Noura M., Heil S., Gaedke M. (2019) Webifying Heterogenous Internet of Things Devices. In: Bakaev M., Frasincar F., Ko IY. (eds) Web Engineering. ICWE 2019. Lecture Notes in Computer Science, vol 11496. Springer, Cham
