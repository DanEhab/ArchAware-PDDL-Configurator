(define (domain Depot)
(:requirements :strips :typing)
(:types place locatable - object
	depot distributor - place
        truck hoist surface - locatable
        pallet crate - surface)

(:predicates (on ?x - crate ?y - surface)
             (in ?x - crate ?y - truck)
             (lifting ?x - hoist ?y - crate)
             (at ?x - locatable ?y - place)
             (clear ?x - surface)
             (available ?x - hoist))

(:action Drop 
:parameters (?x - hoist ?y - crate ?z - surface ?p - place)
:precondition (and (at ?x ?p) (at ?z ?p) (clear ?z) (lifting ?x ?y))
:effect (and (on ?y ?z) (at ?y ?p) (clear ?y) (available ?x) (not (lifting ?x ?y)) (not (clear ?z))))

(:action Load
:parameters (?x - hoist ?y - crate ?z - truck ?p - place)
:precondition (and (at ?x ?p) (at ?z ?p) (lifting ?x ?y))
:effect (and (in ?y ?z) (available ?x) (not (lifting ?x ?y))))

(:action Unload 
:parameters (?x - hoist ?y - crate ?z - truck ?p - place)
:precondition (and (at ?x ?p) (at ?z ?p) (available ?x) (in ?y ?z))
:effect (and (lifting ?x ?y) (not (in ?y ?z)) (not (available ?x))))

(:action Lift
:parameters (?x - hoist ?y - crate ?z - surface ?p - place)
:precondition (and (at ?x ?p) (at ?y ?p) (available ?x) (clear ?y) (on ?y ?z))
:effect (and (lifting ?x ?y) (clear ?z) (not (on ?y ?z)) (not (at ?y ?p)) (not (clear ?y)) (not (available ?x))))

(:action Drive
:parameters (?x - truck ?y - place ?z - place) 
:precondition (and (at ?x ?y))
:effect (and (at ?x ?z) (not (at ?x ?y))))
)