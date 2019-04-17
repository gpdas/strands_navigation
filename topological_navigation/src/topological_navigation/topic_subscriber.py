import sys
import rospy
import rostopic
from threading import Thread


class TopicSubscriberHelper(object):
    """
    Helper class for localise by topic subcription. Callable to start subsriber
    thread.
    """
    def __init__(self, topic, callback, callback_args):
        self.topic = rospy.get_namespace() + topic
        self.callback = callback
        self.callback_args = callback_args
        self.sub = None
        self.t = None


    def get_topic_type(self, topic, blocking=False):
        """
        Get the topic type.
        !!! Overriden from rostopic !!!

        :param topic: topic name, ``str``
        :param blocking: (default False) block until topic becomes available, ``bool``

        :returns: topic type, real topic name and fn to evaluate the message instance
          if the topic points to a field within a topic, e.g. /rosout/msg. fn is None otherwise. ``(str, str, fn)``
        :raises: :exc:`ROSTopicException` If master cannot be contacted
        """
        topic_type, real_topic, msg_eval = rostopic._get_topic_type(topic)
        if topic_type:
            return topic_type, real_topic, msg_eval
        elif blocking:
            sys.stderr.write("WARNING: topic [%s] does not appear to be published yet\n"%topic)
            while not rospy.is_shutdown():
                topic_type, real_topic, msg_eval = rostopic._get_topic_type(topic)
                if topic_type:
                    return topic_type, real_topic, msg_eval
                else:
                    rostopic._sleep(10.0) # Change! Waiting for 10 seconds instead of 0.1 to reduce load
        return None, None, None

    def __call__(self):
        """
        When called start a new thread that waits for the topic type and then
        subscribes. This is therefore non blocking and waits in the background.
        """
        self.t = Thread(target=self.subscribe)
        self.t.start()

    def subscribe(self):
        """
        Get the topic type and subscribe to topic. Subscriber is kept alive as
        long as the instance of the class is alive.
        """
        rostopic.get_topic_type = self.get_topic_type # Monkey patch
        topic_type = rostopic.get_topic_class(self.topic, True)[0]
        rospy.loginfo("Subscribing to %s" % self.topic)
        self.sub = rospy.Subscriber(
            name=self.topic,
            data_class=topic_type,
            callback=self.callback,
            callback_args=self.callback_args
        )


    def close(self):
        self.sub.unregister()

    def __del__(self):
        self.close()
