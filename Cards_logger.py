import logging

cards_logger = logging.getLogger('cards_logger')
cards_logger.setLevel(logging.INFO)

cards_handler = logging.FileHandler('cards_logger.log', mode='w')
cards_formatter = logging.Formatter('%(name)s %(asctime)s %(levelname)s %(message)s')

cards_handler.setFormatter(cards_formatter)
cards_logger.addHandler(cards_handler)
