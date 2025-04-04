"""
Objects Games dialogues
    The dialogues part of this corpus was inspired by the Columbia Games Corpus [3, 4, 5].
    In this part, pairs of subjects were asked to play a series of Objects Games. Each
    subject used a separate laptop computer and could not see the screen of the other
    subject. Subjects sat facing each other in a booth, with an opaque curtain hanging
    between them, so that all communication was verbal.

    In an Objects Game, each subject’s laptop displayed a game board with 5–7 objects,
    as shown in Figure 1. Both subjects saw the same set of objects at the same position on
    the screen, except for one (the target). One subject (the describer) was instructed to
    describe the position of a target object on her screen to the other (the follower), whose
    task was to position the same object on her own screen. Subjects could discuss freely
    about the location of the target object, and were later awarded 1–100 points based
    on how well the follower’s target location matched the Describer’s. Subjects were told
    that their goal was to accumulate as many points as possible over the entire session,
    since they would be paid additional money for each point they earned. Appendix A.1
    includes snapshots of the instructions and sample screens of the Objects Games.

Direction-giving monologues:
    The monologues part of this corpus was inspired by the Boston Directions Corpus [7, 6].
    Subjects were first asked to perform a series of five increasingly complex direction-giving
    tasks, ranging from explaining simple routes such as getting from one station to another
    on the subway, to planning a round trip journey from the University to two Buenos
    Aires tourist sights.
    Subjects were provided with written instructions (Appendix B.1), as well as three
    city maps (snapshots of Google Maps) and a subway map (Appendix B.2). They were
    asked to address the directions to a friend of theirs, as if they were leaving a message
    in their friend’s answering machine. Additionally, subjects were told to assume that
    their addressee was unaware of the descriptions given in the preceding tasks. With this
    procedure, we collected five spontaneous monologues from each subject.
    The elicited speech was orthographically transcribed, with false starts, filled pauses
    and other speech errors repaired or omitted, and punctuation marks and capitalization
    added. All subjects returned a few days after their first session, and were asked to read
    their transcriptions aloud. In this way, we collected read versions of all monologues.

Sessions and subjects:
    The recordings were conducted in two batches, as summarized in Table 1. The first
    batch was collected in November-December, 2012, in a soundproof booth at the Laboratorio de Investigaciones Sensoriales2
    (Hospital de Cl´ınicas, UBA), by Agust´ın Gravano.

    In this batch, a total of 14 subjects participated in exactly two sessions, each of which
    lasted approximately one hour. In their first session, each subject completed the five
    direction-giving tasks described above (spontaneous monologues), followed by 14 instances of the Objects Games (spontaneous dialogues), with subjects alternating in the
    describer and follower roles. In their second session, each subject read the transcriptions of their direction-giving tasks (read monologues), and played 14 new instances
    of the Objects Games (spontaneous dialogues), with a different partner. Only speech
    recordings were collected in this first batch.

    The second batch was recorded in April, 2014, in a booth at the Laboratorio de
    Neurociencia Integrativa (Departamento de F´ısica, FCEyN, UBA), by Juan E. Kamienkowski and Agust´ın Gravano. In this case, 20 subjects participated in just one session
    consisting of a series of 17-30 instances of the Objects Game (spontaneous dialogues).
    In this batch, simultaneous recordings of speech and electroencephalography (EEG)
    activity were collected from each participant. EEG recordings are not included in the
    present release, but may be shared upon request to the authors. The setup of the EEG equipment demanded 30 minutes. We asked subjects to complete a minimum 15
instances of the Objects Game, which typically took 15-30 minutes. After that, given
the discomfort caused by the EEG equipment, we gave subjects the option to stop or
continue, up to a maximum of 30 instances.
In all cases, the subjects’ speech was not restricted in any way, and it was emphasized at the session beginning that the game was not timed. At the end of the session,
subjects were paid a fixed amount of money for their participation, plus a bonus based
on the number of points awarded in the Objects Games.
All subjects were native speakers of Argentine Spanish, lived in the Buenos Aires
area at the time of the study. In the first batch of sessions (monologues and dialogues;
audio only recordings), 14 subjects participated in the study (7 female, 7 male), with
ages ranging from 19 to 59 years (M = 28.6, SD = 12.7); all but one subjects were
right handed. In the second batch of sessions (dialogues only; audio+EEG recordings),
20 subjects took part (10 female, 10 male), age ranging between 19 and 43 years
(M = 26.4, SD = 6.3), and 18 were right-handed. Detailed information about subjects
may be found in the subjects-info.csv and sessions-info.csv files.
Batch 1 contains 71 minutes of spontaneous direction-giving monologue, 48 minutes
of read monologue, and 386 minutes (6.4 hours) of task-oriented dialogue. Batch 2
contains 320 minutes (5.3 hours) of dialogue.

Corpus files
The UBA Games Corpus includes the files listed in Table 2. There is an important difference in the organization of files in batches 1 and 2. For the dialogues
in batch 1, there is one file per session (and speaker). In this way, the file
sNN.objects.1.{A,B}.wav (with NN=01..14) corresponds to the audio for the entire
session NN (and speaker A/B); this file includes all 14 game tasks in that session. The
file sNN.objects.1.{A,B}.tasks specifies the start and end times of each game task,
as explained below.
The dialogues in batch 2 are organized differently. In this case, there is one file
per game task (and speaker). The file sNN.objects.TT.{channel1,channel2}.wav
(with NN=21..30) corresponds to the audio for task number TT (with TT=01..30), speaker
A (channel1) or B (channel2). That is, the sessions are split into separate files for each
game task

Batch 1, dialogue:
b1-dialogue-wavs/ Audio files.
b1-dialogue-tasks/ Information about the game tasks.
b1-dialogue-words/ Orthographic transcriptions, with temporal alignment
at the word level.
b1-dialogue-phrases/ Orthographic transcriptions, with temporal alignment
at the IPU level.
b1-dialogue-turns/ Turn-taking annotations.
Batch 1, monologue Batch 1, monologue:
b1-monologue-wavs/ Audio files.
b1-monologue-texts/ Orthographic transcriptions, with no temporal alignment.
Batch 2, dialogue Batch 2, dialogue:
b2-dialogue-wavs/ Audio files.
b2-dialogue-phrases/ Orthographic transcriptions, with temporal alignment
at the IPU level.
b2-dialogue-turns/ Turn-taking annotations.
Table 2: Files included in this release of the corpus.

Audio files
The audio for each subject was recorded on a separate channel of a TASCAM DR-100
digital recorder, at a sampling rate of 44.1 kHz with 16-bit precision, using a Rode
HS-1 head-mounted close-talking microphone. Each channel was later downsampled to
16 kHz and saved as a separate mono wav file.

Orthographic transcriptions
All speech recordings were orthographically transcribed by trained annotators. All
dialogues were manually time-aligned to the audio files at the IPU level (batches 1 and
2), and at the word level (only batch 1). An inter-pausal unit (IPU) is defined as
a maximal speech segment from a single speaker that is surrounded by pauses longer
than 100 ms.
For the monologues in batch 1, the transcriptions were made from the spontaneous
direction-giving tasks. False starts, filled pauses and other speech errors were repaired
or omitted, and punctuation marks were added. These transcriptions were later used
for the read tasks, and have not been time-aligned to the audio files.
The time-aligned transcriptions are plain text files with one interval per line. Each
interval has following format: <start> <end> <text>, where <start> and <end> are
the time boundaries of the interval, expressed in seconds, and <text> is the transcription of the interval. The special symbol # is used for indicating a silent interval.

Example of a transcription with time-alignment at the word level Example of a transcription with time-alignment at the word level:
b1-dialogue-words/s01.objects.1.A.words
0.000000 0.410000 #
0.410000 0.680000 bueno
0.680000 1.223913 est´a
1.223913 1.540000 #
1.540000 1.712226 el
1.712226 2.181653 mimo
2.181653 3.330000 #
3.330000 3.629761 est´a
3.629761 4.340000 titilando
4.340000 4.694193 #
4.694193 5.083623 arriba
5.083623 5.219060 de
5.219060 5.310000 la
5.310000 6.012202 lechuza
6.012202 6.330000 #
...

Example of a transcription with time-alignment at the IPU level:
b1-dialogue-phrases/s01.objects.1.A.phrases
0.0 0.41 #
0.41 1.223913 bueno est´a
1.223913 1.54 #
1.54 2.181653 el mimo
2.181653 3.33 #
3.33 4.34 est´a titilando
4.34 4.694193 #
4.694193 6.012202 arriba de la lechuza
6.012202 6.33 #

Tasks files
The files in b1-dialogue-tasks/ (batch 1) contain the task structure for the corresponding audio file. These are plain text files with one interval per line. Each interval
corresponds to a game task and has the following format: <start> <end> <info>,
where <start> and <end> are the time boundaries of the task, expressed in seconds,
and <info> has a sequence of one or more of the following commands, separated by
semicolons:

Images:image1,image2,image3,... - Image set used in this game task. There
are three possible image sets:
◦ eye, mirror, bluemoon, nun, ruler, lemon, yellowmoon;
◦ yellowlion, ear, mime, nail, bluelion, owl, lawnmower;
◦ yellowmermaid, mm, iron, onion, whale, bluemermaid, lime.
• Describer:A/B - Which player describes the location of the target image. The
other one listens to the description, and tries to place the target image in its
correct location.

Target:image - Specifies the target image for the current turn.
• Score:points - Number of points earned in this task (from 0 to 100).
• Time-used:NUMBER - Time used to complete this task, computed from the moment the players clicked ‘CONTINUE’ to begin the task, until when they clicked
‘DONE’ to confirm the location of the object. Note that this may differ from the
length of the task interval, computed as <end> − <start>.

In this case, the special symbol # is used for indicating an interval with silence and/or
comments made by the speakers in between tasks.

Example: b1-dialogue-tasks/s01.objects.1.tasks
0.000000 0.046000 #
0.046000 42.061000 Images:yellowlion,ear,mime,nail,bluelion,owl,
lawnmower;Describer:A;Target:mime;Score:99;Time-used:47.107
42.061000 45.468000 #
...
251.996490 296.680000 Images:eye,mirror,bluemoon,nun,ruler,lemon,
yellowmoon;Describer:B;Target:yellowmoon;Score:97;Time-used:45.669
296.680000 299.711000 #
...

The files in b2-dialogue-tasks/ (batch 2) are somewhat different. They also
contain one game task per line, but with this format: <task number> <info>. In this
case, <task number> refers to the task number in this session, from 01 to 30, and
<info> has the same information as described above.
Example Example: b2-dialogue-tasks/s21.objects.tasks
01 Images:yellowlion,ear,mime,nail,bluelion,owl,lawnmower;Describer:A;
Target:mime;Score:88;Time-used:73.109
...
06 Images:eye,mirror,bluemoon,nun,ruler,lemon,yellowmoon;Describer:B;
Target:yellowmoon;Score:94;Time-used:307.991

Turn-taking annotations
The files in b1-dialogue-turns/ and b2-dialogue-turns/ contain the annotations of
turn-taking transition types. These are plain text files with one interval per line. Each
interval corresponds to a conversational turn and has the following format: <start>
<end> <label>, where <start> and <end> are the time boundaries of the turn, expressed in seconds, and <label> is a turn-taking label.
A turn is defined as a maximal sequence of IPUs from one speaker, such that between any two adjacent IPUs there is no speech from the interlocutor. Turns were automatically delimited on the time-aligned orthographic annotations, and subsequently
all transitions from one turn to the next were labeled by trained annotators following
the guidelines shown in Figure 2. A more detailed description of the annotation procedure may be found in [1] and [2]. It is important to note that the Hold transitions
mentioned in these papers (i.e. when the current speaker continues talking after a short pause) are not included in these manual annotations, given that they can be trivially
identified from the time-aligned transcriptions.
Example Example: s01.objects.1.B.turns
2.432062 2.847086 BC
2.847086 10.555597 #
10.555597 11.840000 S
11.840000 13.398680 #
13.398680 18.850000 S
18.850000 20.210000 #
20.210000 22.850361 X3
22.850361 25.036480 #
25.036480 25.744563 S
25.744563 27.264241 #
27.264241 32.590516 S
32.590516 33.474562 #
33.474562 41.652187 X3
48.226493 50.196367 X1
50.196367 51.647250 #
51.647250 52.737983 X2
52.737983 53.057480 #

In this file, each label indicates the transition type from the previous turn (by the other
speaker) to the current turn. For example, the turn that starts roughly at 2.43 seconds
is a backchannel, and the turn that starts at 10.56 seconds is a smooth switch.

The subjects_info.csv file looks like:
subject_id,gender,age,writing_hand
101,female,22,left
102,female,20,right
103,male,21,right
104,female,54,right
105,female,32,right
106,female,21,right
...


The sessions_info.csv file looks like:
session_id,batch,subject_id_A,subject_id_B
1,1,101,102
2,1,103,104
3,1,105,106
4,1,107,108
5,1,109,110
6,1,104,102
7,1,111,112
8,1,110,113
9,1,106,101
10,1,108,105
...
"""

## Let's create a library to parse the corpus and load it into a dictionary.
from pathlib import Path
import os
import zipfile
import requests
import pandas as pd
import logging


class Task:
    def __init__(
        self,
        task_id,
        session_id,
        images,
        describer,
        target,
        score,
        time_used,
        turn_transitions,
        ipus,
        wavs,
    ):
        self.task_id = task_id
        self.session_id = session_id
        self.images = images
        self.describer = describer
        self.target = target
        self.score = score
        self.time_used = time_used
        self.turn_transitions = turn_transitions
        self.ipus = sorted(ipus, key=lambda x: x.start)
        self.wavs = wavs
        self.text = "\n\t" + "\n\t".join([str(ipu) for ipu in self.ipus])

    def __repr__(self):
        return f"Task({self.task_id}, {self.session_id}, {self.describer}, {self.target}, {self.score}, {self.time_used}, {len(self.ipus)} IPUs, {len(self.wavs)} wavs)"

    def __getitem__(self, key):
        return getattr(self, key)


class Session:
    def __init__(self, session_id, batch, subject_a, subject_b, tasks):
        self.session_id = session_id
        self.batch = batch
        self.subject_a = subject_a
        self.subject_b = subject_b
        self.tasks = tasks

    def __repr__(self):
        return f"Session({self.session_id}, {self.batch}, {self.subject_a}, {self.subject_b}, {len(self.tasks)} tasks)"

    def __getitem__(self, key):
        return getattr(self, key)


class Word:
    def __init__(self, start: int, end: int, text: str, speaker: str):
        self.start = start
        self.end = end
        self.text = text
        self.speaker = speaker
        self.duration = end - start

    def __repr__(self):
        return f"Word({self.start}, {self.end}, {self.text})"

    def __getitem__(self, key):
        return getattr(self, key)


class IPU:
    def __init__(self, words: list[Word]):
        self.words = words
        self.start = words[0].start
        self.end = words[-1].end
        self.speaker = words[0].speaker
        self.duration = self.end - self.start
        self.text = " ".join([word.text for word in words])
        self.num_words = len(words)

    def __repr__(self):
        return f"[{self.start}:{self.end}] {self.speaker}: {self.text}"

    def __getitem__(self, key):
        return getattr(self, key)


class TurnTransitionType:
    HOLD = "H"
    SMOOTH_SWITCH = "S"
    BACKCHANNEL = "BC"
    PAUSED_INTERRUPTION = "PI"

    OVERLAPPED_SMOOTH_SWITCH = "O"
    OVERLAPPED_BACKCHANNEL = "BC_O"
    OVERLAPPED_INTERRUPTION = "I"
    OVERLAPPED_BUTTIN_IN = "BI"

    SPECIAL_LABEL_X1 = "X1"  # Used to flag the first turn of the session.
    SPECIAL_LABEL_X2 = "X2"  # Used to flag the non-overlapping transition that continues a BC or a BC_O.
    SPECIAL_LABEL_X2_O = (
        "X2_O"  # Used to flag the overlapping transition that continues a BC or a BC_O.
    )
    SPECIAL_LABEL_X3 = "X3"  # Used to flag simultaneus start of two turns.


class TurnTransition:
    def __init__(self, label: TurnTransitionType, ipu_from: IPU, ipu_to: IPU):
        self.label = label
        self.ipu_from = ipu_from
        self.ipu_to = ipu_to
        self.duration = ipu_to.start - ipu_from.end
        self.overlapped_transition = self.duration < 0

    def __repr__(self):
        return f"TurnTransition({self.label}, {self.ipu_from}, {self.ipu_to})"


class SpanishGamesCorpusDialogues:
    def __init__(self):
        self.corpus_raw = None
        self.sessions = None
        self.corpus_url = (
            "https://www.utdt.edu/ia/integrantes/agravano/UBA-Games-Corpus/"
        )
        self.corpus_local_path = None

        # Corpus files:
        self.corpus_files = {
            "b1-dialogue-phrases": "b1-dialogue-phrases.zip",
            "b1-dialogue-tasks": "b1-dialogue-tasks.zip",
            "b1-dialogue-turns": "b1-dialogue-turns.zip",
            "b1-dialogue-wavs": "b1-dialogue-wavs.zip",
            "b1-dialogue-words": "b1-dialogue-words.zip",
            "b2-dialogue-phrases": "b2-dialogue-phrases.zip",
            "b2-dialogue-tasks": "b2-dialogue-tasks.zip",
            "b2-dialogue-turns": "b2-dialogue-turns.zip",
            "b2-dialogue-wavs": "b2-dialogue-wavs.zip",
            "sessions-info": "sessions-info.csv",
            "subjects-info": "subjects-info.csv",
        }
        self.info = {
            "name": "UBA Games Corpus",
            "short_name": "uba-games",
            "description": "The UBA Games Corpus includes the files listed in Table 2. There is an important difference in the organization of files in batches 1 and 2. For the dialogues in batch 1, there is one file per session (and speaker). In this way, the file sNN.objects.1.{A,B}.wav (with NN=01..14) corresponds to the audio for the entire session NN (and speaker A/B); this file includes all 14 game tasks in that session. The file sNN.objects.1.{A,B}.tasks specifies the start and end times of each game task, as explained below.",
            "language": "Spanish",
            "participants": "Native speakers of Argentine Spanish",
            "age_range": "19-59 years",
        }

        self.banned_sessions = set([28])

    def load(self, url=None, load_audio=False, local_path=None):
        # Load the corpus from the specified URL and parse it into a dictionary
        # If the corpus has been downloaded already, it only loads it.
        # If local path is provided, it saves/load the corpus to/from that path.
        if url:
            self.corpus_url = url

        if local_path:
            self.corpus_local_path = Path(local_path)
        else:
            self.corpus_local_path = Path(f"./.{self.info['short_name']}/")

        self.corpus_local_path.mkdir(parents=True, exist_ok=True)

        if not load_audio:
            self.corpus_files = {
                k: v for k, v in self.corpus_files.items() if not k.endswith("-wavs")
            }

        # Download the corpus files
        self._download()
        # Load the corpus from the downloaded files

        self._load_raw_corpus()
        self._parse_corpus()

    def _download(self):
        # Download the files from the provided url and unzip them:
        for file_id, file_name in self.corpus_files.items():
            if ".zip" in file_name:
                zip_file_path = self.corpus_local_path / file_name
                extracted_folder_path = self.corpus_local_path / file_id

                if extracted_folder_path.exists():
                    print(f"{file_name} already downloaded. Loading it.")
                    continue

                if not zip_file_path.exists():
                    print(f"Downloading {file_name}...")
                    response = requests.get(self.corpus_url + file_name)
                    with open(zip_file_path, "wb") as f:
                        f.write(response.content)

                if not extracted_folder_path.exists():
                    print(f"Unzipping {file_name}...")
                    with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
                        zip_ref.extractall(self.corpus_local_path)

            else:
                # For non-zip files, just download them directly
                file_path = self.corpus_local_path / file_name
                if not file_path.exists():
                    print(f"Downloading {file_name}...")
                    response = requests.get(self.corpus_url + file_name)
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                else:
                    print(f"{file_name} already downloaded. Loading it.")

    def _load_raw_corpus(self):
        # Loads the raw corpus data from the downloaded files into a structured format
        self.corpus_raw = {}
        for file_id, file_name in self.corpus_files.items():
            file_path = self.corpus_local_path / file_name
            if file_name.endswith(".csv"):
                logging.info(f"Loading CSV file: {file_name}")
                self.corpus_raw[file_id] = pd.read_csv(file_path)
            elif file_name.endswith(".zip"):
                folder_path = self.corpus_local_path / file_id
                logging.info(f"Loading extracted ZIP folder: {file_id}")
                self.corpus_raw[file_id] = {}
                for sub_file in os.listdir(folder_path):
                    sub_file_path = folder_path / sub_file
                    self.corpus_raw[file_id][sub_file] = sub_file_path

    def _parse_corpus(self):
        # Parse the raw corpus files into a structured format
        self.sessions = {}
        for session in self.corpus_raw["sessions-info"].itertuples():
            session_id = session.session_id
            if session_id in self.banned_sessions:
                logging.warning(f"Skipping banned session: {session_id}")
                continue
            batch = session.batch
            subject_a = session.subject_id_A
            subject_b = session.subject_id_B
            tasks = self._load_tasks_for_session(
                session_id,
                batch,
            )
            session_obj = Session(session_id, batch, subject_a, subject_b, tasks)
            self.sessions[session_id] = session_obj

    def _load_tasks_for_session(self, session_id, batch):
        tasks = []
        if batch == 1:
            tasks_folder = self.corpus_raw["b1-dialogue-tasks"]
            wav_folder = self.corpus_raw.get("b1-dialogue-wavs")
            phrases_folder = self.corpus_raw["b1-dialogue-phrases"]
            turns_folder = self.corpus_raw["b1-dialogue-turns"]
            words_folder = self.corpus_raw["b1-dialogue-words"]
        elif batch == 2:
            tasks_folder = self.corpus_raw["b2-dialogue-tasks"]
            wav_folder = self.corpus_raw.get("b2-dialogue-wavs")
            phrases_folder = self.corpus_raw["b2-dialogue-phrases"]
            turns_folder = self.corpus_raw["b2-dialogue-turns"]
            words_folder = None
        else:
            logging.error(f"Unknown batch number: {batch}")
            return tasks

        # Load tasks from the tasks file
        sess_idx = f"s{str(session_id).zfill(2)}"  # Ensure session ID is zero-padded to 2 digits
        task_file_id = (
            f"{sess_idx}.objects.1.tasks" if batch == 1 else f"{sess_idx}.objects.tasks"
        )
        tasks_file = tasks_folder.get(task_file_id)

        if not tasks_file:
            raise ValueError(f"Tasks file {task_file_id} not found in {tasks_folder}.")
        tasks_info = load_tasks_info(tasks_file, batch)

        for info in tasks_info:
            task_id = info["Task ID"]
            task_boundaries = (info["Start"], info["End"], task_id, session_id)
            turn_transitions = load_turn_transitions_for_task(
                session_id, task_id, turns_folder, phrases_folder, batch
            )
            wavs = load_wavs_for_task(session_id, task_id, wav_folder)
            ipus = load_ipus_for_task(
                session_id,
                task_id,
                task_boundaries,
                phrases_folder,
                words_folder,
                batch,
            )
            task_obj = Task(
                task_id=task_id,
                session_id=session_id,
                images=info["Images"],
                describer=info["Describer"],
                target=info["Target"],
                score=info["Score"],
                time_used=info["Time-used"],
                turn_transitions=turn_transitions,
                ipus=ipus,
                wavs=wavs,
            )
            tasks.append(task_obj)

        return tasks


def load_tasks_info(tasks_file, batch):
    tasks_info = []

    with open(tasks_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if batch == 1:
                task_info = line.split(";")
                if len(task_info) < 3:
                    continue

                start_end_images, describer, target, score, time_used = task_info
                start, end, images = start_end_images.split(" ")
                start = float(start)
                end = float(end)
                images = images.split("Images:")[-1]  # Handle the "Images:" prefix
                task_id = f"{len(tasks_info) + 1:02d}"
                time_used = float(time_used.split(":")[-1].strip())

            elif batch == 2:
                task_id, task_info = line.split(" ", 1)
                images, describer, target, score, time_used = task_info.split(";")
                start = 0
                time_used = float(time_used.split(":")[-1].strip())
                end = time_used

            images = images.split(",")
            describer = describer.split(":")[-1].strip()
            target = target.split(":")[-1].strip()
            score = score.split(":")[-1].strip()
            tasks_info.append(
                {
                    "Task ID": task_id,
                    "Start": start,
                    "End": end,
                    "Images": images,
                    "Describer": describer,
                    "Target": target,
                    "Score": score,
                    "Time-used": time_used,
                }
            )

    return tasks_info


def load_turn_transitions_for_task(
    session_id, task_id, turns_folder, phrases_folder, batch
):
    for speaker, speaker_suffix in get_speaker_and_suffixes(batch):
        turns_file_id = (
            f"s{session_id:02d}.objects.1.{speaker_suffix}.turns"
            if batch == 1
            else f"s{session_id:02d}.objects.{task_id}.turns.{speaker_suffix}.turns"
        )
        turns_file = turns_folder.get(turns_file_id)
        if not turns_file:
            logging.warning(f"Turn transitions file {turns_file_id} not found.")

    # with open(turns_file, "r", encoding="utf-8") as f:
    # TODO (Make sure turns link to existing IPUs)
    return []


def load_wavs_for_task(session_id, task_id, wav_folder):
    return []


def load_ipus_for_task(
    session_id, task_id, task_boundaries, phrases_folder, words_folder, batch
):
    if batch == 2:
        ipus = load_ipus_from_phrases(session_id, task_id, phrases_folder, batch)
    elif batch == 1:
        ipus = load_ipus_from_words(session_id, task_boundaries, words_folder)

    return ipus


def load_ipus_from_words(session_id, task_boundaries, words_folder):
    task_start = task_boundaries[0]
    task_end = task_boundaries[1]
    all_ipus = []

    for speaker in ["A", "B"]:
        words_file_id = f"s{session_id:02d}.objects.1.{speaker}.words"
        words_file = words_folder[words_file_id]

        words = []
        with open(words_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                parts = line.split(" ")
                if len(parts) == 2:
                    parts = [parts[0], parts[1], "#"]
                else:
                    parts = [x for x in parts if x.strip() != ""]

                t0, tf, text = parts
                t0 = float(t0)
                tf = float(tf)
                text = text.strip()

                if t0 > task_end:
                    break

                if tf < task_start:
                    continue

                if text.strip() == "#":
                    if words:
                        all_ipus.append(IPU(words=words))
                        words = []
                else:
                    words.append(
                        Word(
                            start=float(t0),
                            end=float(tf),
                            text=text.strip(),
                            speaker=speaker,
                        )
                    )
            if words:
                all_ipus.append(IPU(words=words))

    return all_ipus


def elipsis(text, max_length=10):
    """Truncate text to a maximum length and add ellipsis if necessary."""
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text


def get_speaker_and_suffixes(batch):
    if batch == 1:
        return [("A", "A"), ("B", "B")]
    elif batch == 2:
        return [("A", "channel1"), ("B", "channel2")]
    else:
        raise ValueError("Unknown batch number: {}".format(batch))


def load_ipus_from_phrases(session_id, task_id, phrases_folder, batch):
    all_ipus = []
    for speaker, speaker_suffix in get_speaker_and_suffixes(batch):
        ipus_file_id = (
            f"s{session_id:02d}.objects.1.{speaker_suffix}.phrases"
            if batch == 1
            else f"s{session_id:02d}.objects.{task_id}.{speaker_suffix}.phrases"
        )
        ipus_file = phrases_folder.get(ipus_file_id)
        if not ipus_file:
            logging.warning(f"IPUs file {ipus_file_id} not found.")
            continue

        with open(ipus_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                t0, tf, text = line.split("\t")
                if text.strip() == "#":
                    continue
                else:
                    words = [
                        Word(
                            start=float(t0),
                            end=float(tf),
                            text=word.strip(),
                            speaker=speaker,
                        )
                        for word in text.split()
                        if word.strip()
                    ]
                    all_ipus.append(IPU(words=words))

    return all_ipus


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    games_corpus = SpanishGamesCorpusDialogues()
    games_corpus.load(load_audio=True, local_path="./uba_games_corpus/")

    print("Loaded UBA Games Corpus with the following sessions:")
    for session_id, session in games_corpus.sessions.items():
        print(session)
        for task in session.tasks:
            print(f"  {task}")
    # Example to access a specific session and task
    example_session_id = 1
    if example_session_id in games_corpus.sessions:
        example_session = games_corpus.sessions[example_session_id]
        print(
            f"\nExample Task in example Session {example_session_id}: {example_session}"
        )
        task = example_session.tasks[0]
        print(f"  Task {task.task_id}: {task.text} (Score: {task.score})")

    # Note: The above code will load the corpus and print the sessions and tasks.
    # This is a simple demonstration of how to load and access the UBA Games Corpus.
