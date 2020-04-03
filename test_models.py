from dispertech.models.cameras.basler import Camera
from experimentor.models.models import BaseModel


class DummyModel(BaseModel):
    def __init__(self):
        super().__init__()

    def finalize(self):
        print('Finalizing')



if __name__ == "__main__":
    dm = DummyModel.as_process()
    dm2 = DummyModel()
    basler = Camera.as_process('da')
    basler.initialize()

