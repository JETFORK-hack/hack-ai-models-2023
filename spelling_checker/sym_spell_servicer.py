from configparser import ConfigParser
import os
from pathlib import Path
import traceback

from .preprocess import Preprocessor
from .keyboard_layer_translation import KeyboardCorrector
from .symspell_checker import SymSpellChecker


local_path = str(Path(__file__).parent.absolute())


class SymSpellRouterServicer:

    preprocessor = None
    keyboard_inverter = None
    model = None
    config = ConfigParser()

    def __init__(self):
        """ Initialize spelling-checker server and models."""
        super().__init__()
        __class__.get_or_create_model()

    @classmethod
    def get_or_create_model(cls):
        """ Function for building pipeline objects: preprocessor, keyboard inverter, spelling corrector.

        Returns:
            (obj, obj, obj) - preprocessor, keyboard inverter, spelling corrector.
        """
        cls.config.read(os.path.join(local_path, 'config.ini'))
        
        for k in cls.config["DATA_PATH"].keys():
            cls.config.set(
                "DATA_PATH", k,
                os.path.join(local_path, 'mount_files', cls.config["DATA_PATH"][k])
            )
        
        if cls.preprocessor is None:
            cls.preprocessor = Preprocessor()

        if cls.keyboard_inverter is None:
            cls.keyboard_inverter = KeyboardCorrector(cls.config)

        if cls.model is None:
            cls.model = SymSpellChecker(cls.config).load()

        return cls.preprocessor, cls.keyboard_inverter, cls.model

    @staticmethod
    def simple_replace(text: str) -> str:
        """ Replace russian special characters outside preprocessor.

        Args:
            text (str): source string.
        Returns:
            (str): processed string.
        """
        return text.replace("ё", "е")

    def preprocess_and_correct_single(self, params: dict, use_correction: bool) -> str:
        """ Support function for preprocess and correct string.

        Args:
            params (dict): parameters for preprocessing;
            use_correction (bool): use spelling correction.
        Returns:
            (str): processed string.
        """
        res = self.preprocessor.run(**params)
        if use_correction:
            return self.model.suggest(res)
        return res

    def predict_single_correction(
        self, request: str, use_preprocessing: bool, use_keyboard_inverter: bool, use_correction: bool
    ) -> tuple(str, str):
        """ Generate prediction for single input request.

        Args:
            request (str) - input request with preprocessing parameters.
        Returns:
            (str)
        """

        result: str = request

        params = {
            "text": request,
            "inverter": self.keyboard_inverter.translate_sentence if use_keyboard_inverter else None,
            "use_preprocessing": use_preprocessing
        }

        try:
            result = self.preprocess_and_correct_single(params, use_correction)
            result = self.simple_replace(result)
        except:
            print(traceback.format_exc())

        return request, result
