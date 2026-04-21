from system.router import route_input
from system.inference import run_inference
from system.explain import explain

path = input("Enter file path: ")

type_ = route_input(path)
result = run_inference(path, type_)

print(result)
print(explain(result))
