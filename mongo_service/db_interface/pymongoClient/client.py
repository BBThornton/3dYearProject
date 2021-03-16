# import the MongoClient class
from pymongo import MongoClient, errors

class dbClient:

    def __init__(self):
        self.client = self.start_connection()
        self.database = self.client["metagenomic"]

    def start_connection(self):
        try:
            # try to instantiate a client instance
            client = MongoClient(
                host='database',
                port=27017,
                serverSelectionTimeoutMS=3000,  # 3 second timeout
            )
            return client
        except errors.ServerSelectionTimeoutError as err:
            # catch pymongo.errors.ServerSelectionTimeoutError
            print("pymongo ERROR:", err)

    def insert_one(self,data,collection):
        coll = self.database[collection]
        coll.update(data, data, upsert=True);

    def insert_many(self, data, collection):
        coll = self.database[collection]

        coll.update_many(data,data,upsert=True)

    def query(self,query, collection):
        coll = self.database[collection]
        docs = coll.find(query)
        return docs

    def check_doc_exists(self,query,collection):
        coll = self.database[collection]
        if coll.count_documents(query,limit=1) == 0:
            return False
        else:
            return True

    def new_experiment(self,json_object):
        coll = self.database["experiment"]
        coll.insert_one(json_object)

    def get_one(self,query, collection):
        coll = self.database[collection]
        docs = coll.find_one(query)
        return docs

    def get_one_selective(self,query, return_fields, collection):
        coll = self.database[collection]
        docs = coll.find_one(query,return_fields)
        return docs

    def post_order_traversal(self,node,visited):
        coll = self.database["experiment"]
        visited.append(node["_id"])
        current_children = [i for i in coll.find({"parent": node["_id"]})]

        if len(current_children)>0:
            for child in current_children:
                if child["_id"] not in visited:
                    return current_children+self.post_order_traversal(child,visited)
        else:
            return []


    def get_specified_parent_stage(self,target_stage,experiments,visited):
        #TODO LOOP THROUGH CHILDREN FOR UNEVEN TREE
        coll = self.database["experiment"]
        parent = coll.find_one({"_id":experiments[0]["_id"]})
        if parent["stage"] == target_stage:
            return parent
        else:
            visited.append(parent["_id"])
            children = coll.find({"parent":parent["_id"]})
            for child in children:
                if child["_id"] not in visited:
                    all_children = [child]
                    child_return = self.post_order_traversal(child,visited)
                    if child_return is not None:
                        all_children.extend(child_return)
                    experiments.extend(all_children)
            current_exp_parent = coll.find_one({"_id":experiments[0]["parent"]})
            if current_exp_parent["_id"] not in visited:
                experiments.append(current_exp_parent)
            experiments.pop(0)

            return self.get_specified_parent_stage(target_stage,experiments,visited)

    def stage_parent_correct(self,current_stage, parent_experiment):
        coll = self.database["experiment"]
        parent = coll.find_one({"_id":parent_experiment})
        if parent is not None:
            coll = self.database["services"]
            parent_stage = coll.find_one({"_id":current_stage})["parent"]
            if parent["stage"] == parent_stage:
                return parent
        return parent

    def data_collector(self, result_name, stage):
        services = self.database["services"]
        res = services.find_one({"_id": stage})["output"]
        if result_name[-4:] == ".qzv":
            return list(res["visuals"]).index(result_name)
        elif result_name[-4:] == ".qza":
            return list(res["data"]).index(result_name)

    def default_output_names(self,stage):
        services = self.database["services"]
        res = services.find_one({"_id": stage})["output"]
        return res


    def close(self):
        self.client.close()

if __name__ == '__main__':
    print("HI")