'''
Created on Sep 9, 2018

@author: graffy
'''

from .core import Orchestra
from .core import Instrument


class Harmony(Orchestra):

    def __init__(self):
        instruments = [
            Instrument('c piccolo', player='flutist', order=1.000),
            Instrument('c flute', player='flutist', order=1.001),
            Instrument('oboe', player='oboeist', order=2.000),
            Instrument('english horn', player='oboeist', order=2.001),
            Instrument('bassoon', player='bassoonist', order=3.000),
            Instrument('eb clarinet', player='clarinetist', order=4.000),  # aka Eb sopranino clarinet
            Instrument('eb alto clarinet', player='clarinetist', order=4.001, is_rare=True),
            Instrument('bb clarinet', player='clarinetist', order=4.002),  # aka Bb soprano clarinet, most common clarinet
            Instrument('bb bass clarinet', player='clarinetist', order=4.003),
            Instrument('bb contrabass clarinet', player='clarinetist', order=4.004, is_rare=True),
            Instrument('eb contrabass clarinet', player='clarinetist', order=4.005, is_rare=True),

            Instrument('bb soprano saxophone', player='saxophonist', order=5.000),
            Instrument('eb alto saxophone', player='saxophonist', order=5.001),
            Instrument('bb tenor saxophone', player='saxophonist', order=5.002),
            Instrument('eb baritone saxophone', player='saxophonist', order=5.003),

            Instrument('bb trumpet', player='trumpetist', order=6.000),
            Instrument('bb cornet', player='trumpetist', order=6.001),
            Instrument('bb flugelhorn', player='trumpetist', order=6.002),

            Instrument('f horn', player='hornist', order=7.000),
            Instrument('eb horn', player='hornist', order=7.001, is_rare=True),
            
            Instrument('c trombone', player='trombonist', order=8.000),
            Instrument('bb trombone', player='trombonist', order=8.001, is_rare=True),
            Instrument('c bass trombone', player='trombonist', order=8.002),
            Instrument('bb bass trombone', player='trombonist', order=8.003),

            Instrument('c baritone horn', player='euphonist', order=9.000),  # aka 'baritone' 'euphonium'
            Instrument('bb baritone horn', player='euphonist', order=9.001),  # aka 'baritone' 'euphonium'

            Instrument('c tuba', player='tubist', order=10.000),  # actually a f tuba but players read c parts
            Instrument('bb contrabass tuba', player='bbtubist', order=10.001),
            Instrument('c bass', player='tubist', order=10.002),
            Instrument('bb bass', player='bbtubist', order=10.003),
            Instrument('eb bass', player='tubist', order=10.004, is_rare=True),
            Instrument('bb tuba', player='tubist', order=10.005),
            Instrument('eb tuba', player='tubist', order=10.006),
            
            Instrument('drum set', player='percussionist', order=11.001),
            Instrument('clash cymbals', player='percussionist', order=11.002),  # aka concert cymbals, cymbales frappees : https://en.wikipedia.org/wiki/Clash_cymbals
            Instrument('concert bass drum', player='percussionist', order=11.003),
            Instrument('suspended cymbal', player='percussionist', order=11.004),
            Instrument('bongos', player='percussionist', order=11.005),
            Instrument('shaker', player='percussionist', order=11.006),
            Instrument('snare drum', player='percussionist', order=11.007),
            Instrument('tambourine', player='percussionist', order=11.008),
            Instrument('small crash cymbals', player='percussionist', order=11.009),
            Instrument('ratchet', player='percussionist', order=11.010),
            Instrument('flexatone', player='percussionist', order=11.011),
            Instrument('temple blocks', player='percussionist', order=11.012),
            Instrument('wood block', player='percussionist', order=11.013),
            Instrument('cymbals', player='percussionist', order=11.014),  # TODO: check if they're not the same as crash cymbals
            Instrument('side drum', player='percussionist', order=11.015),
            Instrument('gong', player='percussionist', order=11.016),
            Instrument('castanets', player='percussionist', order=11.017),
            Instrument('claves', player='percussionist', order=11.018),
            Instrument('vibraslap', player='percussionist', order=11.019),
            Instrument('congas', player='percussionist', order=11.020),
            Instrument('slide whistle', player='percussionist', order=11.021),
            Instrument('toms', player='percussionist', order=11.022),
            Instrument('tam tam', player='percussionist', order=11.023),
            Instrument('whip', player='percussionist', order=11.024),
            Instrument('slap stick', player='percussionist', order=11.025),
            Instrument('cabaza', player='percussionist', order=11.026),
            Instrument('crotales', player='percussionist', order=11.027),  # https://en.wikipedia.org/wiki/Crotales
            Instrument('finger cymbals', player='percussionist', order=11.028),  # https://en.wikipedia.org/wiki/Zill (sagattes, sagates, ou zil )
            
            Instrument('bells', player='percussionist', order=11.100),  # mallet percussion
            Instrument('bell tree', player='percussionist', order=11.101),
            Instrument('chimes', player='percussionist', order=11.102),
            Instrument('wind chimes', player='percussionist', order=11.103),
            Instrument('triangle', player='percussionist', order=11.104),
            Instrument('sleigh bells', player='percussionist', order=11.105),
            Instrument('cowbell', player='percussionist', order=11.106),
            Instrument('tubular bells', player='percussionist', order=11.107),

            Instrument('mallet percussion', player='percussionist', order=11.200),
            Instrument('xylophone', player='percussionist', order=11.201),
            Instrument('marimba', player='percussionist', order=11.202),
            Instrument('vibraphone', player='percussionist', order=11.203),  # vibraphone (also known as the vibraharp or simply the vibes)
            Instrument('glockenspiel', player='percussionist', order=11.204),

            Instrument('timpani', player='percussionist', order=11.300),  # timbales

            Instrument('string bass', player='bassist', order=12.000, is_rare=True),
            Instrument('electric guitar', player='guitarist', order=12.001, is_rare=True),
        
            Instrument('piano', player='pianist', order=13.000),
            Instrument('synthesizer', player='pianist', order=13.001),
            
            Instrument('voice', player='singer', order=1.000, is_rare=True)]
        
        Orchestra.__init__(self, instruments)
