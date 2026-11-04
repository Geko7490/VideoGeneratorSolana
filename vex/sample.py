"""Hand-authored reference scene, explicitly not an AI planning result."""
from .models import Camera, Keyframe, Node, Project, Scene, Track

STORY = "A small robot wakes up in an abandoned city. It looks around, walks toward a glowing tower, and discovers a mysterious message."


def example_project():
    scenes = []
    for index, (title, narration) in enumerate([
        ("AWAKENING", "In a city forgotten by time, a small robot wakes up."),
        ("THE SIGNAL", "A glowing tower calls from beyond the empty streets."),
        ("A NEW BEGINNING", "Inside the light, a message waits. You are not alone."),
    ]):
        nodes = [
            Node(id="moon", kind="ellipse", x=1030, y=125, width=100, height=100, color="#c3b6f7"),
            Node(id="ground", kind="rectangle", x=640, y=640, width=1280, height=160, color="#22273c", layer=2),
        ]
        for n, (x, h) in enumerate([(80, 280), (225, 190), (400, 350), (600, 235), (790, 310), (1170, 260)]):
            nodes.append(Node(id=f"building{n}", kind="building", x=x, y=560-h/2, width=110, height=h, color="#242942", stroke="#4a496b", layer=1))
        nodes.extend([
            Node(id="tower", kind="tower", x=1010, y=365, width=120, height=385, color="#595274", stroke="#a5f3fc", layer=2),
            Node(id="robot", kind="robot", x=300 + index * 160, y=510, width=95, height=152, color="#a78bfa", stroke="#a5f3fc", layer=3,
                 tracks=[Track(property="x", keys=[Keyframe(time=0, value=300+index*160), Keyframe(time=4, value=460+index*160)])]),
            Node(id="title", kind="text", x=640, y=85, width=1050, height=60, text=title, color="#ece8ff", layer=4,
                 tracks=[Track(property="opacity", keys=[Keyframe(time=0, value=0), Keyframe(time=1, value=1)])]),
        ])
        if index == 2:
            nodes.append(Node(id="message", kind="text", x=860, y=240, width=700, height=55, text="YOU ARE NOT ALONE", color="#a5f3fc", layer=4))
        scenes.append(Scene(id=f"scene{index+1}", title=title, narration=narration, duration=4, camera=Camera(pan_x=18), nodes=nodes))
    return Project(title="The Last Signal", story=STORY, scenes=scenes)
