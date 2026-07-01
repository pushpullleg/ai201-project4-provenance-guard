Milestone 1: Understand the System and Define Your Architecture

⏰ ~30 min

Before touching any code, understand the problem deeply and make your core architectural decisions. Provenance Guard has seven distinct features that need to work together. If you start building without understanding how they connect — how a submission flows through detection to a transparency label, how an appeal flows through to the audit log — you'll end up with a system that works feature-by-feature but breaks at the seams.


Read the required features list in full. Then write, in plain English, the path a single piece of text takes from submission to the label a user sees. Name every system component it touches and what each one does. This is your architecture narrative — you'll use it in your planning.md and README.


Decide on your two detection signals before you write any code. For each signal, write: what property of the text it measures, why that property differs between human and AI writing, and what it can't capture (every signal has blind spots). If you can't describe the blind spot, you don't understand the signal yet.


Think through the false positive problem: what happens when your system misclassifies a human writer's work? Trace that scenario through your system — how does the confidence score reflect the uncertainty, what does the label say, and how does the creator appeal? This scenario should inform your decisions in Milestone 2.


Sketch (on paper or in a text file) your API surface: what endpoints do you need? What does each one accept and return? You're not writing code yet — you're defining the contract that all other code will implement.


Turn your architecture narrative into a diagram. Draw the two main flows: (1) submission flow — POST /submit → signal 1 → signal 2 → confidence scoring → transparency label → audit log → response; (2) appeal flow — POST /appeal → status update → audit log → response. Label each arrow with what passes between components (raw text, signal score, combined score, label text). You'll include this diagram in your planning.md and use it as context when prompting AI tools to generate code.

📍 Checkpoint

You can describe the path a submitted piece of text takes through your system from start to finish, naming every component. You have chosen 2 detection signals and can explain what each captures and what it misses. You have a rough list of the API endpoints you need to build. You have a diagram showing both the submission and appeal flows.