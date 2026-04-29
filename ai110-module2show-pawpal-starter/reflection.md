# PawPal+ Project Reflection

## 1. System Design

Three Core Actions User Should Be Able To Perform: 
- Register a pet, including adding care needs for the pet with frequency and priority.
- See a task list/daily schedule and be able to mark tasks complete.
- Be able to input your availability so tasks can be scheduled around your schedule but in a way the pet's priorities are taken care of.

Brainstorm of Main Objects: 
- Pet
- Task
- User's Schedule Items
- Day (Schedule)

Main Objects with Attributes + Methods
- Pet (Name, Species, Age, Care_Tasks) [UpdateAge, GetAllTasks, AddCareTask, RemoveCareTask]
- Task (Name, Type, Priority, Duration, Frequency, Time_Preference, Status) [AssignPriority, AssignDuration, AssignFrequency, AssignTimePreference, MarkComplete, MarkIncomplete]
- Owner (Name, Availability) [AddAvailability, GetFreeSlots]
- AvailabilityBlock (Label, Start_Time, End_Time, Frequency) [UpdateStart, UpdateEnd, AddFrequency]
- ScheduledTask (Task, Start_Time, End_Time, Is_Complete) [MarkComplete, UpdateStart, UpdateFinish]
- DayPlan (Date, Owner, Pet, Scheduled_Tasks) [AddTask, GetCompletionStatus, Display]
- Scheduler (Owner, Pet, Date, Day_Start, Day_End) [BuildSchedule, PrioritizeTasks, FindAvailableSlot, ExplainPlan]

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

My initial brainstorm had 4 objects pet, task, user's schedule items and day or schedule. The idea was pet had to have an entity and each task needed one. I wanted to have the user's scheudle so that would be one and there should be like a day with all its items. After that I mainly just brainstormed basic items and then I talked to claude for a bit. Now its what you see above. The parenthesis are the attributes and the brackets are the methods to mostly set those attributes. 


**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Yeah but only once, I think I started with a very good setup so it didnt need much change. I think I mostly added the Day start and Day end to scheduler since that was also needed. This particular bottleneck was identified with the help of claude. 

---


## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

Basically we consider the owner's work schedule or busy time, each tasks time preference like morning, afternoon, evening and the priority of the task. Priority matters teh most since those items would be handled with more importance than work. So tasks like feeding or medication gets scheduled before teh lower priority tasks like grooming and stuff. Time preference comes after that to really fit to the app user's life and to make the map more useful overall. 

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

One tradeoff made is having the scheduler scan for open slots in 15 minute increments. This means that if there is a free window that starts at 8:05 it gets skipped. I feel like for pet care tasks precision of time isn't that essential and 15 minute chunks is ok. 

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used it a lot to brainstorm, sort of like a partner who knows everything going on. I would write some things down or put some of my ideas down and be like what do you think, and then I would either agree or disagree with the AI and we would drop it or further discuss. I think I really like using prompts like use the perspective of a senior software engineers, ensure following good coding practicies, make sure things are neat and easy to follow, or from the perspective of a UX designer. Things like that are really helpful. 


**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

I think a lot of the times I ask AI to tell me what its going to do or disucss first before making changes and that way I can disagree without worrying about rollback. It also helps me evaluate and verify what its doing and ensuring that we both are on the same page. 

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

We tested 43 behaviors across every major class: task lifecycle (complete/incomplete/recurrence), pet CRUD, JSON persistence roundtrip, availability conflict detection, the full scheduling algorithm (priority ordering, busy block avoidance, time preference windows), the energy curve (species-based defaults), task batching and batch splitting, day load detection with deferral suggestions, cross-pet conflict detection with resolution suggestions, sort order, and explain output.

These tests mattered because the scheduler has several interacting systems that were easy to break when adding or making changes so these ensured the basic functionality was still in place, I also made sure to go back and add test cases after every major implementation. 

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

I think the core scheduling logic is solid, I tried to keep it simple while making sure all the moving parts worked well together so that everything was clean, smooth, and functional. I think maybe api tests or checking the fall back options for when a task's preferred window is entirely blocked and when tasks are longer than available gaps and things like that. 

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

I think I'm really satisfied with the UI, I even added a night mode, though I havent tested that part yet. 

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

Maybe an autosync with another calendar would be really cool and helpful to the owner. And of course having this available as an app on a phone would be helpful too. 

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
Go step by step, and really know what the AI is about to do. Commit after every feature is polished and then move on to next feature it really helps keep the context focused and as you want it I think.

---

## 6. Prompt Comparison — Multi-Model Analysis

**Task tested:** Implement a `next_occurrence` method on a `Task` dataclass that returns a new Task due on the next date based on frequency (daily = +1 day, weekly = +7 days, as needed = None).

---

**ChatGPT (GPT-4o)**

Went with a basic if/elif chain, readable but not very extensible. Adding a new frequency means going back into the method which isnt great. Also missed resetting status to incomplete on the new task, which matters a lot here.

**Gemini**

Had the most interesting approach, used `frozen=True` with `replace()` so you dont have to pass every field to the constructor again, pretty clean. But frozen=True would break the app since tasks need to be mutated when marking complete. Good idea wrong context.

**Claude**

Used a `FREQUENCY_DELTAS` dict at the module level and just calls `.get()` on it. Adding a new frequency is one line, no method changes needed. Also the only one that reset status to incomplete and kept all the fields. Tradeoff is unknown frequencies fail silently which is less explicit than chatgpts error raise.

---

**Which was most Pythonic?**

Depends on context honestly. Gemini's pattern is cleaner in isolation but doesnt fit the codebase. Claude's fits how the rest of the system is built. Chatgpt's is easiest to read but hardest to grow. None of them are wrong, they just didnt have full context so they solved a slightly different version of the problem.
