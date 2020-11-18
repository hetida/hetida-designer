CREATE TABLE Component(
    Id UUID NOT NULL PRIMARY KEY,
    GroupId UUID,
    Name VARCHAR(255),
    Description VARCHAR(255),
    Category VARCHAR(255),
    Tag VARCHAR(255),
    State VARCHAR(255),
    Code TEXT,
    FunctionName VARCHAR(255),
    TestInput TEXT
);

CREATE TABLE ComponentIO(
    Id UUID NOT NULL PRIMARY KEY,
    Name VARCHAR(255),
    Type VARCHAR(255),
    PosX INTEGER,
    PosY INTEGER
);

CREATE TABLE ComponentInput_To_ComponentIO(
    ComponentId UUID NOT NULL REFERENCES Component (Id),
    ComponentIOId UUID NOT NULL REFERENCES ComponentIO (Id),
    UNIQUE (ComponentId, ComponentIOId)
);

CREATE TABLE ComponentOutput_To_ComponentIO(
    ComponentId UUID NOT NULL REFERENCES Component (Id),
    ComponentIOId UUID NOT NULL REFERENCES ComponentIO (Id),
    UNIQUE (ComponentId, ComponentIOId)
);

CREATE TABLE Workflow(
    Id UUID NOT NULL PRIMARY KEY,
    Category VARCHAR(255),
    Description VARCHAR(255),
    GroupId UUID,
    Name VARCHAR(255),
    State VARCHAR(255),
    Tag VARCHAR(255),
    TestInput TEXT
);

CREATE TABLE WorkflowIO(
    Id UUID NOT NULL PRIMARY KEY,
    Name VARCHAR(255),
    Type VARCHAR(255),
    Connector UUID NOT NULL,
    Operator UUID NOT NULL,
    PosX INTEGER,
    PosY INTEGER,
    Constant BOOLEAN,
    ConstantValue TEXT
);

CREATE TABLE WorkflowInput_To_WorkflowIO(
    WorkflowId UUID NOT NULL,
    WorkflowIOId UUID NOT NULL REFERENCES WorkflowIO (Id),
    UNIQUE (WorkflowId, WorkflowIOId)
);

CREATE TABLE WorkflowOutput_To_WorkflowIO(
    WorkflowId UUID NOT NULL,
    WorkflowIOId UUID NOT NULL REFERENCES WorkflowIO (Id),
    UNIQUE (WorkflowId, WorkflowIOId)
);

CREATE TABLE WorkflowOperator(
     Id UUID NOT NULL PRIMARY KEY,
     ItemId UUID,
     Name VARCHAR(255),
     PosX INTEGER,
     PosY INTEGER,
     Type VARCHAR(255)
);

CREATE TABLE WorkflowLink(
    Id UUID NOT NULL PRIMARY KEY,
    FromConnector UUID NOT NULL,
    FromOperator UUID NOT NULL,
    ToConnector UUID NOT NULL,
    ToOperator UUID NOT NULL
);

CREATE TABLE Workflow_To_WorkflowLink(
    WorkflowId UUID NOT NULL REFERENCES Workflow (Id),
    WorkflowLinkId UUID NOT NULL REFERENCES WorkflowLink (Id),
    UNIQUE (WorkflowId, WorkflowLinkId)
);



CREATE TABLE Workflow_To_WorkflowOperator(
    WorkflowId UUID NOT NULL REFERENCES Workflow (Id),
    WorkflowOperatorId UUID NOT NULL REFERENCES WorkflowOperator (Id),
    UNIQUE (WorkflowId, WorkflowOperatorId)
);

CREATE TABLE Point(
    Id UUID NOT NULL PRIMARY KEY,
    PosY INTEGER,
    PosX INTEGER,
    SequenceNr INTEGER
);

CREATE TABLE WorkflowLink_To_Point(
    WorkflowLinkId UUID NOT NULL REFERENCES WorkflowLink (Id),
    PointId UUID NOT NULL REFERENCES Point (Id),
    UNIQUE (WorkflowLinkId, PointId)
);

CREATE TABLE Documentation(
    Id UUID NOT NULL PRIMARY KEY,
    Document TEXT
);

-- Wiring Tables

CREATE TABLE Wiring(
    Id UUID NOT NULL PRIMARY KEY,
    Name VARCHAR(255)
);

CREATE TABLE ComponentWiring(
    ComponentId UUID NOT NULL REFERENCES Component(Id),
    WiringId UUID NOT NULL REFERENCES Wiring(Id),
    UNIQUE (ComponentId, WiringId)
);

CREATE TABLE WorkflowWiring(
    WorkflowId UUID NOT NULL REFERENCES Workflow(Id),
    WiringId UUID NOT NULL REFERENCES Wiring(Id),
    UNIQUE (WorkflowId, WiringId)
);

CREATE TABLE OutputWiring(
    Id UUID NOT NULL PRIMARY KEY,
    WiringId UUID NOT NULL REFERENCES Wiring(Id),
    WorkflowOutputName VARCHAR(255) NOT NULL,
    AdapterId varchar(255),
    SinkId VARCHAR(255)
);

CREATE TABLE InputWiring(
    Id UUID NOT NULL PRIMARY KEY,
    WiringId UUID NOT NULL REFERENCES Wiring(Id),
    WorkflowInputName VARCHAR(255) NOT NULL,
    AdapterId varchar(255),
    SourceId VARCHAR(255)
);

CREATE TABLE Filter(
    InputWiringId UUID NOT NULL REFERENCES InputWiring(Id),
    Key VARCHAR(255) NOT NULL,
    Value VARCHAR(255) NOT NULL,
    PRIMARY KEY (InputWiringId, Key)
);