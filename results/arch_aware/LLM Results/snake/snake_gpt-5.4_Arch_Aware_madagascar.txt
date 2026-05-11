(define (domain snake)
(:requirements :strips :negative-preconditions :equality)
(:constants
    dummypoint
)
(:predicates
    (ispoint ?x)
    (spawn ?x)
    (NEXTSPAWN ?x ?y)
    (headsnake ?x)
    (tailsnake ?x)
    (nextsnake ?x ?y)
    (blocked ?x)
    (ISADJACENT ?x ?y)
)
(:action move-and-eat-spawn
    :parameters (?head ?newhead ?spawnpoint ?nextspawnpoint)
    :precondition
    (and
        (headsnake ?head)
        (ISADJACENT ?head ?newhead)
        (ispoint ?newhead)
        (spawn ?spawnpoint)
        (NEXTSPAWN ?spawnpoint ?nextspawnpoint)
        (not (blocked ?newhead))
        (not (= ?spawnpoint dummypoint))
    )
    :effect
    (and
        (ispoint ?spawnpoint)
        (spawn ?nextspawnpoint)
        (blocked ?newhead)
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (not (headsnake ?head))
        (not (ispoint ?newhead))
        (not (spawn ?spawnpoint))
    )
)

(:action move-and-eat-no-spawn
    :parameters (?head ?newhead)
    :precondition
    (and
        (headsnake ?head)
        (ISADJACENT ?head ?newhead)
        (ispoint ?newhead)
        (spawn dummypoint)
        (not (blocked ?newhead))
    )
    :effect
    (and
        (blocked ?newhead)
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (not (headsnake ?head))
        (not (ispoint ?newhead))
    )
)

(:action move
    :parameters (?head ?newhead ?tail ?newtail)
    :precondition
    (and
        (headsnake ?head)
        (ISADJACENT ?head ?newhead)
        (tailsnake ?tail)
        (nextsnake ?newtail ?tail)
        (not (blocked ?newhead))
        (not (ispoint ?newhead))
    )
    :effect
    (and
        (blocked ?newhead)
        (headsnake ?newhead)
        (nextsnake ?newhead ?head)
        (tailsnake ?newtail)
        (not (headsnake ?head))
        (not (blocked ?tail))
        (not (tailsnake ?tail))
        (not (nextsnake ?newtail ?tail))
    )
)

)