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
            Instrument('g alto flute', player='flutist', order=1.002, is_rare=True),
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
            Instrument('bb bass saxophone', player='saxophonist', order=5.004, is_rare=True),

            Instrument('bb trumpet', player='trumpetist', order=6.000),
            Instrument('bb cornet', player='trumpetist', order=6.001),
            Instrument('bb flugelhorn', player='trumpetist', order=6.002),
            Instrument('c trumpet', player='trumpetist', order=6.003, is_rare=True),

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
            Instrument('woodblock', player='percussionist', order=11.013),
            Instrument('cymbals', player='percussionist', order=11.014),  # TODO: check if they're not the same as crash cymbals
            Instrument('side drum', player='percussionist', order=11.015),
            Instrument('gong', player='percussionist', order=11.016),
            Instrument('castanets', player='percussionist', order=11.017),
            Instrument('claves', player='percussionist', order=11.018),
            Instrument('vibraslap', player='percussionist', order=11.019),
            Instrument('congas', player='percussionist', order=11.020),
            Instrument('toms', player='percussionist', order=11.022),  # https://en.wikipedia.org/wiki/Tom-tom_drum
            Instrument('tam-tam', player='percussionist', order=11.023),  # https://en.wikipedia.org/wiki/Gong#Chau_gong_(Tam-tam)
            Instrument('whip', player='percussionist', order=11.024),
            Instrument('slap stick', player='percussionist', order=11.025),
            Instrument('cabasa', player='percussionist', order=11.026),  # aka cabaza
            Instrument('crotales', player='percussionist', order=11.027),  # https://en.wikipedia.org/wiki/Crotales
            Instrument('finger cymbals', player='percussionist', order=11.028),  # https://en.wikipedia.org/wiki/Zill (sagattes, sagates, ou zil )
            Instrument('rumberas', player='percussionist', order=11.029),
            Instrument('crash cymbals', player='percussionist', order=11.030),
            Instrument('anvil', player='percussionist', order=11.031),
            Instrument('hi-hat cymbals', player='percussionist', order=11.032),
            Instrument('guiro', player='percussionist', order=11.033),
            Instrument('ocean drum', player='percussionist', order=11.034),
            Instrument('rainstick', player='percussionist', order=11.035),
            Instrument('bell cymbal', player='percussionist', order=11.036),  # aka bell splash cymbal or ice bell https://en.wikipedia.org/wiki/Bell_cymbal
            Instrument('finger cymbal tree', player='percussionist', order=11.037),  # string of suspended finger cymbals
            Instrument('meinl spark shaker', player='percussionist', order=11.038),  # https://www.soundtravels.co.uk/p-Meinl_Spark_Shaker-2824.aspx
            Instrument('timbales', player='percussionist', order=11.039),  # aka pailas https://en.wikipedia.org/wiki/Timbales
            Instrument('sizzle cymbal', player='percussionist', order=11.040),  # https://en.wikipedia.org/wiki/Sizzle_cymbal 
            Instrument('maracas', player='percussionist', order=11.041),
            Instrument('bodhran', player='percussionist', order=11.042),
            Instrument('chinese cymbal', player='percussionist', order=11.043),
            Instrument('sand shaker', player='percussionist', order=11.044),
            Instrument('medium suspended cymbal', player='percussionist', order=11.045),
            Instrument('small suspended cymbal', player='percussionist', order=11.046),

            Instrument('bells', player='percussionist', order=11.100),  # mallet percussion
            Instrument('bell tree', player='percussionist', order=11.101),
            Instrument('chimes', player='percussionist', order=11.102),
            Instrument('wind chimes', player='percussionist', order=11.103),
            Instrument('triangle', player='percussionist', order=11.104),
            Instrument('small triangle', player='percussionist', order=11.105),
            Instrument('sleigh bells', player='percussionist', order=11.106),
            Instrument('cowbell', player='percussionist', order=11.107),
            Instrument('tubular bells', player='percussionist', order=11.108),
            Instrument('tibetan bowl', player='percussionist', order=11.109),  # aka standing bell or resting bell https://en.wikipedia.org/wiki/Standing_bell
            Instrument('mark tree', player='percussionist', order=11.110),  # aka chime tree or bar chimes, https://en.wikipedia.org/wiki/Mark_tree
            Instrument('bike horn', player='percussionist', order=11.111),

            Instrument('mallet percussion', player='percussionist', order=11.200),
            Instrument('xylophone', player='percussionist', order=11.201),
            Instrument('marimba', player='percussionist', order=11.202),
            Instrument('vibraphone', player='percussionist', order=11.203),  # vibraphone (also known as the vibraharp or simply the vibes)
            Instrument('glockenspiel', player='percussionist', order=11.204),
            Instrument('mbira', player='percussionist', order=11.205),  # aka kalimba or finger piano https://en.wikipedia.org/wiki/Mbira

            Instrument('timpani', player='percussionist', order=11.300),  # timbales

            Instrument('slide whistle', player='percussionist', order=11.400),
            Instrument('train whistle', player='percussionist', order=11.401),

            # not set to rare because david the tuba player can use them, so we want one in the print
            Instrument('double bass', player='bassist', order=12.000),  # other names : Bass, upright bass, string bass, acoustic bass, acoustic string bass, contrabass, contrabass viol, bass viol, standup bass, bull fiddle, doghouse bass and bass fiddle, contrebasse
            Instrument('bass guitar', player='bassist', order=12.001),  # other names : Bass, electric bass guitar, electric bass

            Instrument('electric guitar', player='guitarist', order=12.002, is_rare=True),

            Instrument('piano', player='pianist', order=13.000),
            Instrument('synthesizer', player='pianist', order=13.001),
            Instrument('toy piano', player='pianist', order=13.002),

            Instrument('harp', player='harpist', order=14.000),

            Instrument('bb violin', player='violinist', order=15.000, is_rare=True),
            Instrument('bb viola', player='violinist', order=15.001, is_rare=True),
            Instrument('bb cello', player='violinist', order=15.002, is_rare=True),

            Instrument('voice', player='singer', order=1.000, is_rare=True)]

        Orchestra.__init__(self, instruments)
