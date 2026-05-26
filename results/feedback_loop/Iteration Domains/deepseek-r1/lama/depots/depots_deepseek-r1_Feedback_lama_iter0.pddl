(define (domain Depot)
(:requirements :strips :typing)
(:types place locatable - object
	depot distributor - place
        truck hoist surface - locatable
        pallet crate - surface)

(:predicates (at ?x - locatable ?y - place) 
             (on ?x - crate ?y - surface)
             (in ?x - crate ?y - truck)
             (clear ?x - surface)
             (lifting ?x - hoist ?y - crate)
             (available ?x - hoist))
	
(:action Drive
:parameters (?x - truck ?y - place ?z - place) 
:precondition (and (at ?x ?y))
:effect (and (at ?x ?z) (not (at ?x ?y))))

(:action Load
:parameters (?x - hoist ?y - crate ?z - truck ?p - place)
:precondition (and (lifting ?x ?y) (at ?x ?p) (at ?z ?p))
:effect (and (in ?y ?z) (available ?x) (not (lifting ?x ?y))))

(:action Unload 
:parameters (?x - hoist ?y - crate ?z - truck ?p - place)
:precondition (and (in ?y ?z) (available ?x) (at ?x ?p) (at ?z ?p))
:effect (and (lifting ?x ?y) (not (in ?y ?z)) (not (available ?x))))

(:action Drop 
:parameters (?x - hoist ?y - crate ?z - surface ?p - place)
:precondition (and (lifting ?x ?y) (clear ?z) (at ?x ?p) (at ?z ?p))
:effect (and (on ?y ?z) (at ?y ?p) (clear ?y) (available ?x) (not (lifting ?x ?y)) (not (clear ?z))))

(:action Lift
:parameters (?x - hoist ?y - crate ?z - surface ?p - place)
:precondition (and (on ?y ?z) (clear ?y) (available ?x) (at ?x ?p) (at ?y ?p))
:effect (and (lifting ?x ?y) (clear ?z) (not (at ?y ?p)) (not (clear ?y)) (not (available ?x)) (not (on ?y ?z))))

)