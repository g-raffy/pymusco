![musco-logo](./logo.svg)

[![Python application](https://github.com/g-raffy/pymusco/actions/workflows/pythonapp.yml/badge.svg)](https://github.com/g-raffy/pymusco/actions/workflows/pythonapp.yml)

# pymusco

`pymusco` is a python application to manage digitised orchestral musical scores.

This tool is aimed at big orchestras, where it's sometimes difficult to deal with sheet music, especially the orchestras that don't give original copies to musicians

## features

By making heavy use of digitized sheet music, `pymusco` provides a way to addresses the following problems:
- when the time of making copies for musicians, computing the number of copies of each track could involve some headscratching, as it requires knowledge of who plays which instrument(s) and who can play which tracks. As a result, if we want the number of copies to be just right, this operation has to be done by someone with sufficient knowledge of the musicians and all types of instruments there are tracks for. With `pymusco`'s solution, the people in charge of printing are just given a print pdf that `pymusco` automatically created; they just need to send this [print-pdf](#print-pdf) to the printer, without more thinking.
- printing copies for musicians is time consuming. `pymusco` makes the printing operation much less time consuming than if the people have to inut the number of copies for each track. And also because they don't have to feed the originals physically on the scanner.
- giving detached copies to musicians can lead to pages that we no longer know to which musical piece they belong to or which page it is in the musical piece. `pymusco` solves this by adding a page information line at the bottom of each print page; this page information line displays:
    - the title of the musical piece
    - the name of the track(s) it contains, (in english: this also helps to deal with foreign sheet music, where sometimes the name of the instrument is not easy to understand for a forreigner. Not a lot of non spanish musicians knows that *requinto* is the spanish name for a E-flat clarinet...) 
    - the page number in the track
    - the number of pages in the track
- ensuring that each copy given to musicians has the stamp of the owner can be tedious. This stamp is important, as it allows from a copy to know who owns the original and therefore if the use of this copy is legitimate or not. `pymusco` eases the stamping process by automatically adding a stamp of each page of the coppies.
- musicians that forget to bring at rehearsals their own copy of the track. This is even more a problem if no other musician has this track.

## disclaimer

Digitizing original sheet music can be illegal depending on countries and editors. `pymusco` encourages in no way to trespass the law. `pymusco` doesn't have to be used with material subject to copyright.

## how to install

```
python ./setup.py install
```

## how to use

`make test` provides a full example that generates a [stub-pdf](#stub-pdf) and a [print-pdf](#print-pdf) from a [scan-pdf](#scan-pdf)

### examples

#### build a stub from a scan

The following command builds the [stub-pdf](#stub-pdf) `$PYMUSCO_WORKSPACE_ROOT/stubs/007-captain-future-galaxy-drift-1.pdf` from the [scan-pdf](#scan-pdf) `$PYMUSCO_WORKSPACE_ROOT/scans/007-captain-future-galaxy-drift-1.pdf` and the [piece description file](#piece-description-file) `$PYMUSCO_WORKSPACE_ROOT/scans/007-captain-future-galaxy-drift-1.desc`:
```bash
PYTHONPATH=./src ./src/apps/pymusco \
   --orchestra-file-path samples/jazz.orchestra \
   build-stub \
   --scan-file-path samples/scans/007-captain-future-galaxy-drift-1.pdf \
   --scan-desc-file-path samples/scans/007-captain-future-galaxy-drift-1.desc \
   --stub-file-path samples/stubs/007-captain-future-galaxy-drift-1.pdf
```
#### build a print pdf from a scan

The following command builds the [print-pdf](#print-pdf) `$PYMUSCO_WORKSPACE_ROOT/prints/007-captain-future-galaxy-drift-1.pdf` from the [stub-pdf](#stub-pdf) `$PYMUSCO_WORKSPACE_ROOT/stubs/007-captain-future-galaxy-drift-1.pdf` and the [headcount file](#ts-auto) `$PYMUSCO_WORKSPACE_ROOT/samples/jazz.headcount`:

```bash
PYTHONPATH=./src ./src/apps/pymusco \
    --orchestra-file-path samples/jazz.orchestra \
    build-print \
    --stub-file-path samples/stubs/007-captain-future-galaxy-drift-1.pdf \
    --print-file-path samples/prints/007-captain-future-galaxy-drift-1.pdf \
    ts-auto --headcount-file-path samples/jazz.headcount
```

## definitions

### scan-pdf

A [scan-pdf](#scan-pdf) is just digitized version of the paper original. It is expected to contain exactly one copy of each track.

### stub-pdf

A [stub-pdf](#stub-pdf) is a pdf file which contains a single sheet music for each track, but unlike the scan, also contains a table of contents listing all the tracks it contains.

### invidividuals-pdf

A [invidividuals-pdf](#invidividuals-pdf) is a pdf file which contains a single sheet music for a unique track. When build these pdf are put in a folder for each type of musician.

### print-pdf

A [print-pdf](#print-pdf) is a pdf file for a musical piece that, as its name suggests, is ready to send for printing on real paper. It contains multiple copies of each track, enough to ensure that each musician has one track assigned.

The selection of tracks that `pymusco` includes in the [print-pdf](#print-pdf) depends on the [track-selector](#track-selectors) that the user chooses.

### piece description file

This file (in **JSON with comments** format) describes the [scan-pdf](#scan-pdf) that it's related to. Here's an example :

```json
{
    "format": "pymusco.piece_description.v1",
    "uid": 7,
    "title": "captain future galaxy drift 1",
    "stamp_descs": [
        {
            "stamp_image_path": "../../logo.pdf",
            "scale": 0.5,
            "tx": 19.5,  // position of the center of the stamp in cm from left of page
            "ty": 28.2   // position of the center of the stampin cm from bottom of page
        }
    ],
    "page_info_line_y_pos" : 1.0,  // from bottom of the page, in cm
    "scan_toc" : {
        "format": "pymusco.toc.v1",
        "track_id_to_page": {
            "bb soprano saxophone": 1,
            "c violin 1": 2,
            "c violin 2": 2,
            "c acoustic guitar": 3,
            "bass guitar": 5,
            "drum set": 6}   // snare drum & cymbal
    },
    "missing_tracks" : {
        "c violin 3": "lost",  // the sheet music for this track is lost
        "eb horn 1": "couldn_t_bother"  // additional parts for certain countries
    }
}
```

### orchestra file

This file is a database of all possible instruments, and uses the format **JSON with comments**. For each instrument, it stores:
- uid: a unique identifier of the instrument
- player: a unique id of the player that is able to play this instrument. This field is typically used by [ts-auto](#ts-auto).
- order: this value is used to order tracks in the [stub-pdf](#stub-pdf)
- is_rare: If true, this intrument is considered rare in the given orchestra type (eg harp in a harmony). This field is used by [ts-auto](#ts-auto).

```json
{
    "format": "pymusco.orchestra.v1",
    "instruments" : [
        { "uid": "bb soprano saxophone", "player": "saxophonist", "order": 5.000 },
        { "uid": "eb alto saxophone", "player": "saxophonist", "order": 5.001 },
        { "uid": "bb tenor saxophone", "player": "saxophonist", "order": 5.002 },
        { "uid": "eb baritone saxophone", "player": "saxophonist", "order": 5.003 },

        { "uid": "f horn", "player": "hornist", "order": 7.000, "is_rare": true },

        { "uid": "drum set", "player": "percussionist", "order": 11.001 },
        { "uid": "clash cymbals", "player": "percussionist", "order": 11.002 },  // aka concert cymbals, cymbales frappees : https://en.wikipedia.org/wiki/Clash_cymbals
        { "uid": "snare drum", "player": "percussionist", "order": 11.007 },

        { "uid": "bass guitar", "player": "bassist", "order": 12.001 },  // other names : Bass, electric bass guitar, electric bass

        { "uid": "electric guitar", "player": "guitarist", "order": 12.002 },
        { "uid": "c acoustic guitar", "player": "guitarist", "order": 12.003 },

        { "uid": "c violin", "player": "violinist", "order": 15.010}
    ]
}
```

### track selectors

The role of a track selector is to choose which tracks to include in the [print-pdf](#print-pdf) and how many copies of them.

#### ts-auto

The number of copies for each track is automatically computed and depends both on the existing tracks in the [stub-pdf](#stub-pdf), and on the headcount of the orchestra.

As an example, in a scenario where there are three trumpet tracks in the [stub-pdf](#stub-pdf) (trumpet 1, trumpet 2 and trumpet 3) and there are 5 trumpettists in the orchestra, `pymusco`'s automatic track selector would put 3 copies of each trumpet track in the print pdf. While 2 copie of each would be more than enough, one extra copy is added for each track for musicians that were given a copy but forgot to bring it on rehearsals (yes, this happens!).

[ts-auto](#ts-auto) track selector requires the user to define a headcount (file format **JSON with comments**) file such as :
```json
{
    "saxophonist": 1,  
    "violinist": 3,  
    "guitarist": 1,
    "bassist": 1,
    "percussionist": 1
}
```

#### ts-single

This simple [track-selector](#track-selectors) allows the user to just include one copy of the track he chooses.
