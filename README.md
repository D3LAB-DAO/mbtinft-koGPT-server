# mbtinft-koGPT-server

> powered by [KakaoBrain KoGPT](https://github.com/kakaobrain/kogpt)

# How to start

## Run server

Install required packages:

```bash
$ python install -r requirements.txt
```

Start server:

```bash
$ cd server
$ python server.py
```
```
 * Serving Flask app 'server' (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: off
 * Running on all addresses.
   WARNING: This is a development server. Do not use it in a production deployment.
 * Running on http://<your_ip_address>:<port_num>/ (Press CTRL+C to quit)
```

`<port_num>` is `33327` as default.

### Curl

```bash
$ curl [-X <method>] [-H 'Content-Type: application/json'] [-d <data>] [other_options...] <server_url>/<call>
```

* `<method>` can be one of `<GET | POST | PUT | PATCH | DELETE>`.
* `<call>` can be one of `<upload | inference | download>` currently.

## Run daemon

TBA

### Curl

TBA

<!--
# Features

## Server

![fig 1. Server overview](./images/fig1.png)

### RESTful API

[`server.py`](./server/server.py)

### DB

`server.db`

### Logging

`server.log`

## Inference

![fig 2. AI system overview](./images/fig2.png)

### Daemon

[`daemon.py`](./inference/daemon.py)

### KoGPT

[`koGPT.py`](./inference/koGPT.py)

### PPLM

Future work.

[`pplm.py`](./inference/pplm.py)
-->

# Contact

Luke Park (Sanghyeon Park)

> [🖥 https://github.com/lukepark327](https://github.com/lukepark327)\
> [✉️ lukepark327@gmail.com](mailto:lukepark327@gmail.com)
