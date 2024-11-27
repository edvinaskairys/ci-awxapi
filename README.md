1) Manually run Github Actions workflow
2) Github Actions runs .py script, which processes arguments.yaml file which has xstatus = 0 and creates a request to Ansible AWX API.
3) After the request was send, .py script set xstatus argument to 1. So the next time it would not be proccessed.
4) Check the example arguments.yaml.example file.




