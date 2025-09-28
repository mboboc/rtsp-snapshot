# rtsp-snapshot
Save a snapshot from an RTSP stream to a local file.

### Installation
Copy config.example.json in config.json and update the file with the
devices information.

```
cp config.example.json config.json
```

### Run the script
```
python rtsp_snapshot.py  --config-file config.json
```

I recommand using a [virutalenv](https://realpython.com/python-virtual-environments-a-primer/) for Python. 
