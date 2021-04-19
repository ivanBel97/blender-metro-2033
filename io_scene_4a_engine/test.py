from model_transform import ModelTransformToBlender


path = input("Model filepath: ")
trans = ModelTransformToBlender(path)

print(trans.faces)
